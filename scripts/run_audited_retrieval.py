"""Measure source-audited draft retrieval without enabling answer scoring."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from rag_system.evaluation.datasets import EvaluationCase
from rag_system.evaluation.metrics import document_matches, retrieval_hit, retrieval_page_hit
from rag_system.evaluation.provenance import run_metadata
from rag_system.evaluation.runner import _inferred_filing_filter
from rag_system.generation.answering import _generation_evidence_sources
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def audited_cases(draft_path, audit_path, original_path):
    """Require unchanged baseline and unambiguous, exact source-page matches."""
    raw = json.loads(draft_path.read_text(encoding="utf-8"))
    original = json.loads(original_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["draft_sha256"] != hashlib.sha256(draft_path.read_bytes()).hexdigest():
        raise ValueError("Source audit is stale; rerun the PDF audit")
    if raw[: len(original)] != original:
        raise ValueError("Original regression cases were changed")
    checks = {item["case_id"]: item for item in audit["cases"]}
    if len({item["case_id"] for item in raw}) != len(raw):
        raise ValueError("Duplicate case IDs")
    cases = []
    for index, item in enumerate(raw):
        pages = item.get("expected_pages", [])
        if index >= len(original):
            pages = []
            for check in checks[item["case_id"]]["page_checks"]:
                matches = [c for c in check["candidates"] if c["evidence_overlap"] == 1.0]
                if len(matches) != 1 or check["document"] != item["expected_document"]:
                    raise ValueError(f"Unresolved source page: {item['case_id']}")
                pages.append(matches[0]["physical_page"])
            if not pages:
                raise ValueError(f"Missing source audit: {item['case_id']}")
        cases.append(
            EvaluationCase(
                item["case_id"],
                item["question"],
                item["expected_answer"],
                item["expected_document"],
                tuple(sorted(set(pages))),
            )
        )
    return cases, len(original)


def summarize(results):
    labelled = [item for item in results if item["page_hit"] is not None]
    return {
        "case_count": len(results),
        "filing_recall": sum(item["filing_hit"] for item in results) / len(results)
        if results
        else None,
        "page_labelled_count": len(labelled),
        "any_evidence_page_recall": sum(item["page_hit"] for item in labelled) / len(labelled)
        if labelled
        else None,
        "all_evidence_pages_recall": sum(item["all_pages_hit"] for item in labelled) / len(labelled)
        if labelled
        else None,
        "generation_context_page_recall": sum(
            bool(item.get("generation_page_hit")) for item in labelled
        )
        / len(labelled)
        if labelled and all("generation_page_hit" in item for item in labelled)
        else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("evaluation/drafts/cases_50.json"))
    parser.add_argument("--audit", type=Path, default=Path("evaluation/drafts/source_audit.json"))
    parser.add_argument("--original", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--vector-store", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Restrict offline diagnostics to explicitly named cases",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    cases, baseline_count = audited_cases(args.cases, args.audit, args.original)
    if args.case_id:
        requested = set(args.case_id)
        available = {case.case_id for case in cases}
        if not requested <= available:
            parser.error("Unknown case ID")
        original_ids = {case.case_id for case in cases[:baseline_count]}
        cases = [case for case in cases if case.case_id in requested]
        baseline_count = sum(case.case_id in original_ids for case in cases)
    metadata = run_metadata(args.cases, args.vector_store, "hybrid", args.top_k)
    metadata["selected_case_ids"] = [case.case_id for case in cases]
    metadata["source_audit_sha256"] = hashlib.sha256(args.audit.read_bytes()).hexdigest()
    metadata["retrieval_code_sha256"] = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path("src/rag_system/retrieval").glob("*.py"))
    }
    started = time.monotonic()
    results = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    store = SQLiteVectorStore(args.vector_store)
    try:
        retriever = HybridRetriever(SentenceTransformerEmbeddingProvider(), store)
        for case in cases:
            routing = _inferred_filing_filter(retriever, case.question)
            retrieved = retriever.retrieve(case.question, args.top_k, routing)
            generation_context = _generation_evidence_sources(case.question, retrieved)
            found = {
                page
                for hit in retrieved
                if document_matches(hit.chunk.document_name, case.expected_document)
                for page in hit.chunk.page_numbers
            }
            results.append(
                {
                    "case_id": case.case_id,
                    "question": case.question,
                    "inferred_filter": routing,
                    "expected_document": case.expected_document,
                    "expected_pages": case.expected_pages,
                    "filing_hit": retrieval_hit(case, retrieved),
                    "page_hit": retrieval_page_hit(case, retrieved),
                    "generation_page_hit": retrieval_page_hit(case, generation_context),
                    "retrieved_chunk_count": len(retrieved),
                    "generation_chunk_count": len(generation_context),
                    "all_pages_hit": set(case.expected_pages) <= found
                    if case.expected_pages
                    else None,
                    "retrieved": [
                        {
                            "chunk_id": hit.chunk.chunk_id,
                            "document": hit.chunk.document_name,
                            "pages": hit.chunk.page_numbers,
                        }
                        for hit in retrieved
                    ],
                }
            )
            payload = {
                "status": "complete" if len(results) == len(cases) else "partial",
                "scope": "Draft retrieval diagnostic only; answers/rubrics not validated. Semantic duplicates may remain. Not a held-out benchmark.",
                "context": "All returned context, including adjacent chunks; top_k counts anchors, not final chunks.",
                "run_metadata": metadata,
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "original": summarize(results[:baseline_count]),
                "additions": summarize(results[baseline_count:]),
                "combined": summarize(results),
                "cases": results,
            }
            args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(
                f"{len(results)}/{len(cases)} {case.case_id}: filing={results[-1]['filing_hit']} page={results[-1]['page_hit']}",
                flush=True,
            )
    finally:
        store.close()


if __name__ == "__main__":
    main()
