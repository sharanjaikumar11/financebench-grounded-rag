"""Dense retrieval components."""

from rag_system.retrieval.embeddings import GeminiEmbeddingProvider
from rag_system.retrieval.retriever import DenseRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore

__all__ = ["DenseRetriever", "GeminiEmbeddingProvider", "SQLiteVectorStore"]
