"""Evaluate grounded Gemini answers against FinanceBench cases."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.runner import EvaluationRunner, GroundedEvaluationSystem
from rag_system.generation.answering import GeminiAnswerProvider, GroundedAnswerGenerator
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import DenseRetriever, HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate grounded Gemini answers against FinanceBench.")
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--vector-store", type=Path, required=True)
    parser.add_argument("--retrieval-mode", choices=("dense", "hybrid"), default="hybrid")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key.strip():
        raise SystemExit("Set GEMINI_API_KEY before running generation evaluation")
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    fallback_model = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
    thinking_level = os.environ.get("GEMINI_THINKING_LEVEL", "low")
    store = SQLiteVectorStore(arguments.vector_store)
    try:
        retriever_class = HybridRetriever if arguments.retrieval_mode == "hybrid" else DenseRetriever
        system = GroundedEvaluationSystem(
            retriever_class(SentenceTransformerEmbeddingProvider(), store),
            GroundedAnswerGenerator(
                GeminiAnswerProvider(api_key, model, fallback_model, thinking_level)
            ),
            arguments.top_k,
        )
        report = EvaluationRunner().run(system, load_evaluation_cases(arguments.cases))
    finally:
        store.close()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")
    print(json.dumps(report.as_dict(), indent=2))


if __name__ == "__main__":
    main()
