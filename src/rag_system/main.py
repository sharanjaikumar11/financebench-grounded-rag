"""Runnable production API composition root."""

from pathlib import Path

from rag_system.api.app import create_app
from rag_system.chunking import FixedTokenChunker
from rag_system.config import Settings
from rag_system.generation.answering import GeminiAnswerProvider, GroundedAnswerGenerator
from rag_system.ingestion.pipeline import DocumentIngestor, DocumentRegistry
from rag_system.logging import configure_logging
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.services.query import RAGQueryService


def build_application(storage_directory: Path = Path("data/processed/local_sentence_transformers")):
    settings = Settings.from_environment()
    configure_logging(settings.log_level)
    api_key = settings.require_gemini_key()
    service = RAGQueryService(
        ingestor=DocumentIngestor(DocumentRegistry(storage_directory / "documents.sqlite3")),
        chunker=FixedTokenChunker(200, 40),
        retriever=HybridRetriever(
            SentenceTransformerEmbeddingProvider(),
            SQLiteVectorStore(storage_directory / "vectors.sqlite3"),
        ),
        answer_generator=GroundedAnswerGenerator(
            GeminiAnswerProvider(api_key, settings.gemini_model)
        ),
        top_k=3,
    )
    return create_app(service)


app = build_application()
