"""Compare both complete chunker indexes on identical reviewed questions."""

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.metrics import retrieval_hit, retrieval_page_hit
from rag_system.evaluation.provenance import run_metadata
from rag_system.evaluation.runner import (
    EvaluationRunner,
    GroundedEvaluationSystem,
    _inferred_filing_filter,
)
from rag_system.generation.answering import (
    GeminiAnswerProvider,
    GroundedAnswerGenerator,
    _generation_evidence_sources,
)
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def inspect_index(path):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        names = {row[0] for row in connection.execute("SELECT DISTINCT document_name FROM chunks")}
        strategies = {
            row[0] for row in connection.execute("SELECT DISTINCT chunking_strategy FROM chunks")
        }
    return names, strategies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixed",
        type=Path,
        default=Path("data/processed/local_sentence_transformers/vectors.sqlite3"),
    )
    parser.add_argument(
        "--section",
        type=Path,
        default=Path("data/processed/local_sentence_transformers_section_aware/vectors.sqlite3"),
    )
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--top-k", type=int, nargs="+", default=[3, 5, 10])
    parser.add_argument(
        "--generation",
        action="store_true",
        help="Calls Gemini; requires a local key. Use --top-k 3 for the required answer comparison.",
    )
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if any(k < 1 for k in args.top_k) or len(set(args.top_k)) != len(args.top_k):
        parser.error("top-K values must be positive and unique")
    if args.output_directory.exists():
        parser.error("Choose a new output directory to preserve previous runs")
    cases = load_evaluation_cases(args.cases)
    if args.generation and not os.getenv("GEMINI_API_KEY", "").strip():
        parser.error("Set GEMINI_API_KEY locally before generation comparison")
    fixed_names, fixed_strategies = inspect_index(args.fixed)
    section_names, section_strategies = inspect_index(args.section)
    if fixed_names != section_names or not fixed_names:
        parser.error("Indexes must contain the same non-empty document set")
    if fixed_strategies != {"fixed_token"} or section_strategies != {"section_aware"}:
        parser.error("Indexes must contain only their stated chunking strategy")
    args.output_directory.mkdir(parents=True)
    embedder = SentenceTransformerEmbeddingProvider()
    provider = None
    if args.generation:
        if os.getenv("ANSWER_PROVIDER", "gemini").lower() != "gemini":
            parser.error("Set ANSWER_PROVIDER=gemini for this Gemini comparison")
        provider = GeminiAnswerProvider(
            os.environ["GEMINI_API_KEY"],
            os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"),
            os.getenv("GEMINI_THINKING_LEVEL", "minimal"),
        )
    for strategy, path in (("fixed_token", args.fixed), ("section_aware", args.section)):
        store = SQLiteVectorStore(path)
        try:
            retriever = HybridRetriever(embedder, store)
            for k in args.top_k:
                started = time.monotonic()
                metadata = run_metadata(args.cases, path, "hybrid", k)
                output = args.output_directory / f"{strategy}_k{k}.json"
                if provider:
                    print(f"Generating {strategy} K={k}: {len(cases)} questions", flush=True)
                    report = (
                        EvaluationRunner()
                        .run(
                            GroundedEvaluationSystem(
                                retriever, GroundedAnswerGenerator(provider), k
                            ),
                            cases,
                        )
                        .as_dict()
                    )
                else:
                    results = []
                    for case in cases:
                        found = retriever.retrieve(
                            case.question, k, _inferred_filing_filter(retriever, case.question)
                        )
                        selected = _generation_evidence_sources(case.question, found)
                        results.append(
                            {
                                "case_id": case.case_id,
                                "filing_hit": retrieval_hit(case, found),
                                "page_hit": retrieval_page_hit(case, found),
                                "generation_page_hit": retrieval_page_hit(case, selected),
                                "context_chunks": len(found),
                            }
                        )
                        print(f"{strategy} K={k} {len(results)}/{len(cases)}", flush=True)
                    labelled = [r for r in results if r["page_hit"] is not None]
                    report = {
                        "case_count": len(results),
                        "filing_recall": sum(r["filing_hit"] for r in results) / len(results),
                        "labelled_page_recall": sum(r["page_hit"] for r in labelled) / len(labelled)
                        if labelled
                        else None,
                        "generation_context_page_recall": sum(
                            r["generation_page_hit"] for r in labelled
                        )
                        / len(labelled)
                        if labelled
                        else None,
                        "cases": results,
                    }
                report.update(
                    {
                        "strategy": strategy,
                        "top_k": k,
                        "corpus_documents": len(fixed_names),
                        "run_metadata": metadata,
                        "elapsed_seconds": round(time.monotonic() - started, 2),
                        "mode": "generation" if provider else "retrieval_only",
                        "context_policy": "Full neighbor-expanded retrieval, generation limited to nine selected chunks",
                    }
                )
                output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(f"Saved {output}", flush=True)
        finally:
            store.close()


if __name__ == "__main__":
    main()
