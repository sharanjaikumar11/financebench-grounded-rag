"""Run reproducible retrieval experiments against a local vector index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.runner import RetrievalExperimentRunner
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import DenseRetriever, HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval against FinanceBench cases.")
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--vector-store", type=Path, required=True)
    parser.add_argument("--chunking-strategy", choices=("fixed_token", "section_aware"), required=True)
    parser.add_argument("--top-k", type=int, required=True)
    parser.add_argument("--retrieval-mode", choices=("dense", "hybrid"), default="dense")
    parser.add_argument(
        "--apply-query-metadata-filter",
        action="store_true",
        help="Restrict retrieval when the question unambiguously identifies a filing company and year.",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    cases = load_evaluation_cases(arguments.cases)
    store = SQLiteVectorStore(arguments.vector_store)
    try:
        retriever_class = HybridRetriever if arguments.retrieval_mode == "hybrid" else DenseRetriever
        retriever = retriever_class(SentenceTransformerEmbeddingProvider(), store)
        report = RetrievalExperimentRunner().run(
            retriever,
            cases,
            arguments.chunking_strategy,
            arguments.top_k,
            apply_query_metadata_filter=arguments.apply_query_metadata_filter,
        )
    finally:
        store.close()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report.as_dict(), indent=2), encoding="utf-8"
    )
    print(json.dumps(report.as_dict(), indent=2))


if __name__ == "__main__":
    main()
