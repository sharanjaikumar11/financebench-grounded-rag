from pathlib import Path

import pytest

from rag_system.chunking import SectionAwareChunker
from rag_system.generation.answering import GroundedAnswerGenerator
from rag_system.ingestion.pipeline import DocumentIngestor, DocumentRegistry
from rag_system.retrieval.retriever import DenseRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.services.query import RAGQueryService


class DeterministicEmbedder:
    def embed(self, texts: list[str]) -> tuple[tuple[float, ...], ...]:
        return tuple(
            (1.0, 0.0) if "revenue" in text.casefold() else (0.0, 1.0)
            for text in texts
        )


class CitedAnswerProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        return "Revenue increased. [S1]"


def service(tmp_path: Path, provider: CitedAnswerProvider) -> RAGQueryService:
    ingestor = DocumentIngestor(DocumentRegistry(tmp_path / "documents.sqlite3"))
    retriever = DenseRetriever(DeterministicEmbedder(), SQLiteVectorStore(tmp_path / "vectors.sqlite3"))
    return RAGQueryService(
        ingestor=ingestor,
        chunker=SectionAwareChunker(chunk_size=30),
        retriever=retriever,
        answer_generator=GroundedAnswerGenerator(provider),
        top_k=3,
    )


def test_query_service_indexes_retrieves_and_returns_a_grounded_answer(tmp_path: Path) -> None:
    source = tmp_path / "report.md"
    source.write_text("# Results\nRevenue increased by 10 percent.", encoding="utf-8")
    provider = CitedAnswerProvider()
    query_service = service(tmp_path, provider)

    indexed = query_service.index_document(source)
    response = query_service.answer("How did revenue change?")

    assert indexed.status == "indexed"
    assert indexed.chunk_count == 1
    assert response.retrieved[0].chunk.document_name == "report.md"
    assert response.answer.insufficient_context is False
    assert response.answer.citations[0].document_name == "report.md"
    assert provider.calls == 1


def test_query_service_preserves_duplicate_protection_and_rejects_empty_questions(tmp_path: Path) -> None:
    source = tmp_path / "report.md"
    source.write_text("# Results\nRevenue increased.", encoding="utf-8")
    query_service = service(tmp_path, CitedAnswerProvider())

    assert query_service.index_document(source).status == "indexed"
    assert query_service.index_document(source).status == "duplicate"
    with pytest.raises(ValueError):
        query_service.answer("   ")


def test_query_service_recovers_an_incomplete_document_index(tmp_path: Path) -> None:
    source = tmp_path / "report.md"
    source.write_text("# Results\nRevenue increased.", encoding="utf-8")
    query_service = service(tmp_path, CitedAnswerProvider())

    first = query_service.index_document(source)
    assert first.document_id is not None
    query_service.retriever.vector_store._connection.execute(
        "DELETE FROM chunks WHERE document_id = ?", (first.document_id,)
    )
    query_service.retriever.vector_store._connection.commit()

    assert query_service.index_document(source).status == "reindexed"
