from pathlib import Path

import pytest

from rag_system.retrieval.retriever import DenseRetriever
from rag_system.retrieval.embeddings import GeminiEmbeddingProvider, SentenceTransformerEmbeddingProvider
from rag_system.retrieval.vector_store import SQLiteVectorStore, VectorStoreError
from rag_system.schemas import DocumentChunk


class TestEmbedder:
    def embed(self, texts: list[str]) -> tuple[tuple[float, ...], ...]:
        vectors = {
            "revenue increased": (1.0, 0.0),
            "operating risk": (0.0, 1.0),
            "revenue query": (0.9, 0.1),
        }
        return tuple(vectors[text] for text in texts)


def chunk(chunk_id: str, document_id: str, text: str, strategy: str = "fixed_token") -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_name=f"{document_id}.pdf",
        chunk_index=0,
        text=text,
        token_count=2,
        chunking_strategy=strategy,
        page_numbers=(1,),
        section_titles=("Overview",),
    )


def test_dense_retriever_returns_ranked_chunks_and_source_metadata(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = DenseRetriever(TestEmbedder(), store)
    retriever.index([
        chunk("revenue", "doc-a", "revenue increased"),
        chunk("risk", "doc-b", "operating risk"),
    ])

    results = retriever.retrieve("revenue query", top_k=2)

    assert [item.chunk.chunk_id for item in results] == ["revenue", "risk"]
    assert results[0].score > results[1].score
    assert results[0].chunk.page_numbers == (1,)
    store.close()


def test_dense_retriever_applies_document_and_strategy_filters(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = DenseRetriever(TestEmbedder(), store)
    retriever.index([
        chunk("revenue", "doc-a", "revenue increased"),
        chunk("risk", "doc-b", "operating risk", strategy="section_aware"),
    ])

    assert [item.chunk.chunk_id for item in retriever.retrieve("revenue query", 3, {"document_id": "doc-b"})] == ["risk"]
    assert retriever.retrieve("revenue query", 3, {"chunking_strategy": "missing"}) == ()
    store.close()


def test_vector_store_rejects_invalid_vectors_filters_and_top_k(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    source = chunk("revenue", "doc-a", "revenue increased")
    with pytest.raises(VectorStoreError):
        store.upsert([source], [(1.0,), (0.0,)])
    with pytest.raises(ValueError):
        store.search((1.0,), 0)
    with pytest.raises(ValueError):
        store.search((1.0,), 1, {"page_number": 1})
    store.close()


def test_dense_retriever_indexes_in_bounded_batches(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = DenseRetriever(TestEmbedder(), store)
    with pytest.raises(ValueError):
        retriever.index([chunk("revenue", "doc-a", "revenue increased")], batch_size=0)
    retriever.index(
        [
            chunk("revenue", "doc-a", "revenue increased"),
            chunk("risk", "doc-b", "operating risk"),
        ],
        batch_size=1,
    )
    assert len(retriever.retrieve("revenue query", 2)) == 2
    store.close()


def test_dense_retriever_detects_complete_document_indexes(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = DenseRetriever(TestEmbedder(), store)
    chunks = [
        chunk("revenue", "doc-a", "revenue increased"),
        chunk("risk", "doc-a", "operating risk"),
    ]
    assert retriever.has_complete_index(chunks) is False
    retriever.index(chunks)
    assert retriever.has_complete_index(chunks) is True
    assert retriever.has_complete_index(chunks[:1]) is False
    store.close()


def test_gemini_embedder_requires_a_key_and_handles_an_empty_batch() -> None:
    with pytest.raises(ValueError):
        GeminiEmbeddingProvider("")
    assert GeminiEmbeddingProvider("test-key").embed([]) == ()


def test_sentence_transformer_embedder_handles_an_empty_batch_without_loading_model() -> None:
    provider = SentenceTransformerEmbeddingProvider()
    assert provider.embed([]) == ()
    assert provider._model is None
