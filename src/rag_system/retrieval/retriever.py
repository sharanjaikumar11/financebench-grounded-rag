"""Dense retrieval orchestration."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from rag_system.retrieval.embeddings import EmbeddingProvider
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.schemas import DocumentChunk, RetrievedChunk


def retrieval_query(question: str) -> str:
    """Add standard financial-statement terminology for retrieval only."""
    normalized = re.sub(r"[^a-z0-9]+", " ", question.casefold()).strip()
    aliases = {
        "capital expenditure": "purchases property equipment additions property equipment cash flows",
        "cost of goods sold": "cost of revenue cost of sales",
        "inventory": "inventories merchandise inventory",
        "total assets": "balance sheet total assets",
        "inventory": "inventories merchandise inventory",
        "total assets": "balance sheet total assets",
        "quick ratio": "cash equivalents accounts receivable current assets current liabilities inventory",
        "net property plant and equipment": "accumulated depreciation property plant equipment net balance sheet",
        "net property plant equipment": "accumulated depreciation property plant equipment net balance sheet",
        "net ppne": "accumulated depreciation property plant equipment net balance sheet",
        "operating-income margin": "operating income net sales operating margin",
        "operating income margin": "operating income net sales operating margin",
    }
    additions = [terms for term, terms in aliases.items() if term in normalized]
    return " ".join((question, *additions))


class DenseRetriever:
    """Embed chunks and queries, then retrieve the most similar source chunks."""

    def __init__(self, embedder: EmbeddingProvider, vector_store: SQLiteVectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def index(self, chunks: Sequence[DocumentChunk], batch_size: int = 32) -> None:
        """Embed and persist chunks in bounded batches for API-safe indexing."""
        if batch_size < 1:
            raise ValueError("batch_size must be at least one")
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self.vector_store.upsert(
                batch,
                self.embedder.embed([chunk.text for chunk in batch]),
            )

    def has_complete_index(self, chunks: Sequence[DocumentChunk]) -> bool:
        """Determine whether a deterministic document/chunker result is already stored."""
        if not chunks:
            return False
        first_chunk = chunks[0]
        return self.vector_store.has_complete_document(
            first_chunk.document_id,
            first_chunk.chunking_strategy,
            len(chunks),
        )

    def retrieve(
        self,
        query: str,
        top_k: int,
        metadata_filter: Mapping[str, object] | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        query_embedding = self.embedder.embed([query])
        if len(query_embedding) != 1:
            raise RuntimeError("Embedding provider must return one vector for a query")
        return self.vector_store.search(query_embedding[0], top_k, metadata_filter)


class HybridRetriever(DenseRetriever):
    """Combine dense similarity with local full-text matching."""

    def retrieve(
        self, query: str, top_k: int, metadata_filter: Mapping[str, object] | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        query_embedding = self.embedder.embed([query])
        if len(query_embedding) != 1:
            raise RuntimeError("Embedding provider must return one vector for a query")
        ranked = self.vector_store.hybrid_search(
            query_embedding[0], retrieval_query(query), top_k, metadata_filter
        )
        return self.vector_store.expand_with_neighbors(ranked)
