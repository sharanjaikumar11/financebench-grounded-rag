"""Evaluate grounded provider answers against FinanceBench cases."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.provenance import run_metadata
from rag_system.evaluation.runner import EvaluationRunner, GroundedEvaluationSystem
from rag_system.generation.answering import (
    GeminiAnswerProvider,
    GroqAnswerProvider,
    GroundedAnswerGenerator,
)
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import DenseRetriever, HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate grounded provider answers against FinanceBench."
    )
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--vector-store", type=Path, required=True)
    parser.add_argument("--retrieval-mode", choices=("dense", "hybrid"), default="hybrid")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--include-provider-output",
        action="store_true",
        help="Store raw provider replies in the local report for debugging; may contain source text.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    # Reject unreviewed cases before loading models or contacting a provider.
    cases = load_evaluation_cases(arguments.cases)
    metadata = run_metadata(
        arguments.cases, arguments.vector_store, arguments.retrieval_mode, arguments.top_k
    )
    provider_name = os.environ.get("ANSWER_PROVIDER", "gemini").strip().casefold()
    if provider_name == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key.strip():
            raise SystemExit("Set GROQ_API_KEY before running generation evaluation")
        provider = GroqAnswerProvider(api_key, os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"))
    elif provider_name == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key.strip():
            raise SystemExit("Set GEMINI_API_KEY before running generation evaluation")
        provider = GeminiAnswerProvider(
            api_key,
            os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"),
            os.environ.get("GEMINI_THINKING_LEVEL", "minimal"),
        )
    else:
        raise SystemExit("ANSWER_PROVIDER must be either 'gemini' or 'groq'")
    store = SQLiteVectorStore(arguments.vector_store)
    try:
        retriever_class = (
            HybridRetriever if arguments.retrieval_mode == "hybrid" else DenseRetriever
        )
        system = GroundedEvaluationSystem(
            retriever_class(SentenceTransformerEmbeddingProvider(), store),
            GroundedAnswerGenerator(
                provider, include_provider_output=arguments.include_provider_output
            ),
            arguments.top_k,
        )
        report = EvaluationRunner().run(system, cases)
    finally:
        store.close()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    payload = report.as_dict()
    payload["run_metadata"] = metadata
    arguments.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
