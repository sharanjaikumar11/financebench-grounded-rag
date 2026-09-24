"""End-to-end document indexing and grounded query workflow."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from rag_system.generation.answering import GroundedAnswerGenerator
from rag_system.ingestion.pipeline import DocumentIngestor
from rag_system.retrieval.query_metadata import filing_metadata_filter
from rag_system.retrieval.retriever import DenseRetriever
from rag_system.schemas import DocumentChunk, GroundedAnswer, RetrievedChunk


class Chunker(Protocol):
    """Produces retrieval-ready chunks from an ingested document."""

    def chunk(self, document: object) -> tuple[DocumentChunk, ...]: ...


@dataclass(frozen=True, slots=True)
class IndexingResult:
    """Outcome of indexing one source document."""

    status: str
    document_id: str | None
    chunk_count: int


@dataclass(frozen=True, slots=True)
class QueryResponse:
    """Grounded response plus the retrieved evidence used to create it."""

    retrieved: tuple[RetrievedChunk, ...]
    answer: GroundedAnswer


class RAGQueryService:
    """Connect ingestion, chunking, dense retrieval, and grounded generation."""

    def __init__(
        self,
        ingestor: DocumentIngestor,
        chunker: Chunker,
        retriever: DenseRetriever,
        answer_generator: GroundedAnswerGenerator,
        top_k: int,
    ) -> None:
        if top_k < 1:
            raise ValueError("top_k must be at least one")
        self.ingestor = ingestor
        self.chunker = chunker
        self.retriever = retriever
        self.answer_generator = answer_generator
        self.top_k = top_k

    def index_document(self, source_path: Path) -> IndexingResult:
        """Ingest, chunk, and persist a new source document exactly once."""
        ingestion = self.ingestor.ingest(source_path, parse_if_duplicate=True)
        if ingestion.document is None:
            raise RuntimeError("Ingested document was unexpectedly absent")

        chunks = self.chunker.chunk(ingestion.document)
        if not chunks:
            raise RuntimeError("Chunking produced no indexable content")
        if ingestion.status == "duplicate" and self.retriever.has_complete_index(chunks):
            return IndexingResult("duplicate", ingestion.document.document_id, len(chunks))
        self.retriever.index(chunks)
        status = "indexed" if ingestion.status == "ingested" else "reindexed"
        return IndexingResult(status, ingestion.document.document_id, len(chunks))

    def answer(
        self, question: str, metadata_filter: Mapping[str, object] | None = None
    ) -> QueryResponse:
        """Retrieve evidence and generate a citation-grounded answer."""
        question = question.strip()
        if not question:
            raise ValueError("A non-empty question is required")
        inferred_filter = filing_metadata_filter(question)
        if not inferred_filter:
            inferred_filter = self.retriever.vector_store.infer_filing_metadata_filter(question)
        combined_filter = dict(inferred_filter)
        combined_filter.update(metadata_filter or {})
        retrieved = self.retriever.retrieve(question, self.top_k, combined_filter)
        return QueryResponse(
            retrieved=retrieved,
            answer=self.answer_generator.answer(question, retrieved),
        )
