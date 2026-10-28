"""Collect all draft answers for evidence review, never publish unreviewed accuracy."""

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from run_audited_retrieval import audited_cases

from rag_system.evaluation.metrics import citation_correct, retrieval_hit, retrieval_page_hit
from rag_system.evaluation.provenance import run_metadata
from rag_system.evaluation.reviewed_scoring import summarize_review
from rag_system.evaluation.runner import GroundedEvaluationSystem
from rag_system.generation.answering import (
    GeminiAnswerProvider,
    GroundedAnswerGenerator,
    safe_error_details,
)
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def select_cases(cases, baseline_count, requested):
    original_ids = {case.case_id for case in cases[:baseline_count]}
    requested = set(requested)
    if requested - {case.case_id for case in cases}:
        raise ValueError("Unknown case ID")
    selected = [case for case in cases if not requested or case.case_id in requested]
    return selected, original_ids


def collection_summary(rows, cases, original_ids):
    original_count = sum(case.case_id in original_ids for case in cases)
    return {
        "original": summarize_review(
            [r for r in rows if r["case_id"] in original_ids], original_count
        ),
        "additions": summarize_review(
            [r for r in rows if r["case_id"] not in original_ids], len(cases) - original_count
        ),
        "combined": summarize_review(rows, len(cases)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Collect only named cases; report as a targeted diagnostic, not a full evaluation",
    )
    parser.add_argument(
        "--vector-store",
        type=Path,
        default=Path("data/processed/local_sentence_transformers/vectors.sqlite3"),
    )
    args = parser.parse_args()
    draft = Path("evaluation/drafts/cases_50.json")
    audit = Path("evaluation/drafts/source_audit.json")
    original = Path("evaluation/cases.json")
    cases, baseline_count = audited_cases(draft, audit, original)
    if len(cases) != 50 or baseline_count != 11:
        parser.error("Expected unchanged original 11 plus 39 additions")
    try:
        cases, original_ids = select_cases(cases, baseline_count, args.case_id)
    except ValueError as error:
        parser.error(str(error))
    if args.output.exists():
        parser.error("Output exists; use a new filename")
    if not args.vector_store.is_file():
        parser.error("Vector store missing")
    if args.preflight_only:
        print(
            f"Preflight passed: {len(cases)} source-audited draft cases; reference review still required; no API calls."
        )
        return
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        parser.error("Set GEMINI_API_KEY locally; never paste it in chat")
    os.environ.update(
        ANSWER_PROVIDER="gemini",
        GROUNDED_OUTPUT_MODE="evidence",
        STATEMENT_AWARE_RANKING="1",
        FINANCIAL_INTENT_RANKING="1",
        CONTEXT_DIVERSITY_RANKING="1",
        RERANKER_MODEL="",
    )
    metadata = run_metadata(draft, args.vector_store, "hybrid", 5)
    metadata["selected_case_ids"] = [case.case_id for case in cases]
    metadata["collection_mode"] = "targeted" if args.case_id else "full_50"
    metadata["audit_sha256"] = hashlib.sha256(audit.read_bytes()).hexdigest()
    metadata["generation_code_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path("src/rag_system/generation").glob("*.py")
    }
    metadata["retrieval_code_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path("src/rag_system/retrieval").glob("*.py")
    }
    provider = GeminiAnswerProvider(
        key,
        os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"),
        os.getenv("GEMINI_THINKING_LEVEL", "minimal"),
    )
    store = SQLiteVectorStore(args.vector_store)
    rows = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        system = GroundedEvaluationSystem(
            HybridRetriever(SentenceTransformerEmbeddingProvider(), store),
            GroundedAnswerGenerator(provider, include_provider_output=True),
            5,
        )
        for case in cases:
            row = {
                "case_id": case.case_id,
                "cohort": "original_11" if case.case_id in original_ids else "added_39",
                "question": case.question,
                "reference_answer": case.expected_answer,
                "expected_document": case.expected_document,
                "expected_pages": case.expected_pages,
                "answer_correct": None,
            }
            try:
                provider.last_diagnostics = {}
                response = system.answer(case.question)
                row.update(
                    status="completed",
                    generated_answer=response.answer.text,
                    abstained=response.answer.insufficient_context,
                    citation_correct=citation_correct(case, response.answer),
                    retrieval_hit=retrieval_hit(case, response.retrieved),
                    retrieval_page_hit=retrieval_page_hit(case, response.retrieved),
                    citations=[asdict(c) for c in response.answer.citations],
                    retrieved=[asdict(c) for c in response.retrieved],
                    diagnostics=response.answer.diagnostics,
                )
            except Exception as error:
                # Never store exception strings that could contain credentials.
                row.update(status="provider_or_pipeline_error", error_type=type(error).__name__)
                row["error_details"] = safe_error_details(error)
                row["provider_diagnostics"] = dict(provider.last_diagnostics)
            rows.append(row)
            payload = {
                "status": "collected" if len(rows) == len(cases) else "partial",
                "scope": ("Targeted diagnostic; not a 50-case evaluation. " if args.case_id else "")
                + "Draft response collection, not approved answer accuracy. Review references before adjudication.",
                "run_metadata": metadata,
                **collection_summary(rows, cases, original_ids),
                "cases": rows,
            }
            args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"{len(rows)}/{len(cases)} {case.case_id}: {row['status']}", flush=True)
    finally:
        store.close()


if __name__ == "__main__":
    main()
