"""Index a directory of supported documents into the local vector store."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from rag_system.chunking import FixedTokenChunker, SectionAwareChunker
from rag_system.generation.answering import GeminiAnswerProvider, GroundedAnswerGenerator
from rag_system.ingestion.pipeline import DocumentIngestor, DocumentRegistry
from rag_system.retrieval.embeddings import GeminiEmbeddingProvider
from rag_system.retrieval.retriever import DenseRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.services.indexing import index_directory
from rag_system.services.query import RAGQueryService


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index PDF, TXT, and Markdown files.")
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("--storage-directory", type=Path, default=Path("data/processed"))
    parser.add_argument("--strategy", choices=("fixed_token", "section_aware"), required=True)
    parser.add_argument("--chunk-size", type=int, required=True)
    parser.add_argument("--overlap", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def build_service(arguments: argparse.Namespace) -> RAGQueryService:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key.strip():
        raise RuntimeError("Set GEMINI_API_KEY before running document indexing")
    embedding_model = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    answer_model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    chunker_class = {
        "fixed_token": FixedTokenChunker,
        "section_aware": SectionAwareChunker,
    }[arguments.strategy]
    storage = arguments.storage_directory
    return RAGQueryService(
        ingestor=DocumentIngestor(DocumentRegistry(storage / "documents.sqlite3")),
        chunker=chunker_class(arguments.chunk_size, arguments.overlap),
        retriever=DenseRetriever(
            GeminiEmbeddingProvider(api_key, embedding_model),
            SQLiteVectorStore(storage / "vectors.sqlite3"),
        ),
        answer_generator=GroundedAnswerGenerator(GeminiAnswerProvider(api_key, answer_model)),
        top_k=arguments.top_k,
    )


def main() -> None:
    arguments = parse_arguments()
    try:
        service = build_service(arguments)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
    result = index_directory(service, arguments.source_directory)
    print(
        {
            "indexed": result.indexed,
            "duplicates": result.duplicates,
            "failed": list(result.failed),
        }
    )
    if result.failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
