from pathlib import Path

import pytest

from rag_system.retrieval.embeddings import (
    GeminiEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from rag_system.retrieval.query_metadata import filing_metadata_filter
from rag_system.retrieval.retriever import (
    DenseRetriever,
    HybridRetriever,
    retrieval_query,
)
from rag_system.retrieval.vector_store import (
    SQLiteVectorStore,
    VectorStoreError,
    _financial_keyword_relevance,
    _sparse_query_terms,
)
from rag_system.schemas import DocumentChunk


class TestEmbedder:
    def embed(self, texts: list[str]) -> tuple[tuple[float, ...], ...]:
        vectors = {
            "revenue increased": (1.0, 0.0),
            "operating risk": (0.0, 1.0),
            "revenue query": (0.9, 0.1),
            "the requested table value": (0.5, 0.5),
        }
        return tuple(vectors[text] for text in texts)


def chunk(
    chunk_id: str,
    document_id: str,
    text: str,
    strategy: str = "fixed_token",
    chunk_index: int = 0,
    document_name: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_name=document_name or f"{document_id}.pdf",
        chunk_index=chunk_index,
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


def test_hybrid_retriever_combines_dense_and_keyword_candidates(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = HybridRetriever(TestEmbedder(), store)
    retriever.index([chunk("revenue", "doc-a", "revenue increased"), chunk("risk", "doc-b", "operating risk")])
    results = retriever.retrieve("revenue query", 2)
    assert results[0].chunk.chunk_id == "revenue"
    store.close()


def test_hybrid_retriever_scopes_dense_search_to_keyword_candidate_documents(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = HybridRetriever(TestEmbedder(), store)
    retriever.index([
        chunk("revenue", "doc-a", "revenue increased"),
        chunk("risk", "doc-b", "operating risk"),
    ])

    results = store.hybrid_search((0.9, 0.1), "revenue query", top_k=2)

    assert [item.chunk.document_id for item in results] == ["doc-a"]
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
    assert [item.chunk.chunk_id for item in retriever.retrieve("revenue query", 3, {"document_name": "doc-a.pdf"})] == ["revenue"]
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


def test_sentence_transformer_embedder_loads_only_from_the_local_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys
    from types import ModuleType

    captured: dict[str, object] = {}

    class FakeSentenceTransformer:
        def __init__(self, model_name: str, **kwargs: object) -> None:
            captured["model_name"] = model_name
            captured.update(kwargs)

        def encode(self, texts: list[str], normalize_embeddings: bool) -> list[list[float]]:
            assert normalize_embeddings is True
            return [[1.0] for _ in texts]

    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    assert SentenceTransformerEmbeddingProvider().embed(["local evidence"]) == ((1.0,),)
    assert captured == {"model_name": "all-MiniLM-L6-v2", "local_files_only": True}


def test_filing_metadata_filter_requires_unambiguous_company_and_fiscal_year() -> None:
    assert filing_metadata_filter("What was FY2018 capital expenditure for 3M?") == {
        "document_name": "3M_2018_10K.pdf"
    }


def test_query_service_prefers_indexed_filing_metadata_over_legacy_text_parsing(
    tmp_path: Path,
) -> None:
    from rag_system.services.query import RAGQueryService

    class NoOpIngestor:
        pass

    class NoOpChunker:
        pass

    class NoOpGenerator:
        def answer(self, question: str, retrieved: tuple[object, ...]) -> object:
            return None

    class CapturingRetriever:
        def __init__(self) -> None:
            self.vector_store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
            self.vector_store.upsert(
                [chunk("microsoft", "doc-microsoft", "Cost of revenue 32,780", document_name="MICROSOFT_2016_10K.pdf")],
                [(1.0, 0.0)],
            )
            self.metadata_filter: object = None

        def retrieve(self, question: str, top_k: int, metadata_filter: object) -> tuple[object, ...]:
            self.metadata_filter = metadata_filter
            return ()

    retriever = CapturingRetriever()
    service = RAGQueryService(NoOpIngestor(), NoOpChunker(), retriever, NoOpGenerator(), 3)
    service.answer("What was Microsoft's FY2016 cost of goods sold?")

    assert retriever.metadata_filter == {"document_name": "MICROSOFT_2016_10K.pdf"}
    retriever.vector_store.close()


def test_vector_store_infers_an_unambiguous_company_and_year_from_indexed_documents(
    tmp_path: Path,
) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    store.upsert(
        [
            chunk(
                "amazon", "doc-amazon", "net income attributable to shareholders",
                document_name="AMAZON_2019_10K.pdf",
            ),
            chunk(
                "boeing", "doc-boeing", "property plant and equipment",
                document_name="BOEING_2018_10K.pdf",
            ),
            chunk(
                "johnson", "doc-johnson", "consumer health discontinued operation",
                document_name="JOHNSON_JOHNSON_2023_8K_dated-2023-08-30.pdf",
            ),
            chunk(
                "jpm-q2", "doc-jpm-q2", "consumer community banking net income",
                document_name="JPMORGAN_2022Q2_10Q.pdf",
            ),
        ],
        [(1.0, 0.0), (0.0, 1.0), (0.5, 0.5), (0.2, 0.8)],
    )

    assert store.infer_filing_metadata_filter(
        "What was Amazon's FY2019 net income attributable to shareholders?"
    ) == {"document_name": "AMAZON_2019_10K.pdf"}
    assert store.infer_filing_metadata_filter("What was FY2019 net income?") == {}
    assert store.infer_filing_metadata_filter(
        "Which Johnson and Johnson business segment was discontinued from August 30, 2023 onward?"
    ) == {"document_name": "JOHNSON_JOHNSON_2023_8K_dated-2023-08-30.pdf"}
    assert store.infer_filing_metadata_filter(
        "In Q2 2022, which JPMorgan business segment had the highest net income?"
    ) == {"document_name": "JPMORGAN_2022Q2_10Q.pdf"}
    store.close()
    assert filing_metadata_filter("What was capital expenditure?") == {}
    assert filing_metadata_filter("Is 3M a capital-intensive business based on FY2022 data?") == {
        "document_name": "3M_2022_10K.pdf"
    }


def test_vector_store_prefers_the_later_annual_filing_for_year_comparisons(
    tmp_path: Path,
) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    store.upsert(
        [
            chunk("walmart-2019-10k", "doc-walmart-10k", "operating income margin", document_name="WALMART_2019_10K.pdf"),
            chunk("walmart-2019-10q", "doc-walmart-10q", "quarterly operating income", document_name="WALMART_2019Q4_10Q.pdf"),
            chunk("amd-2022-10k", "doc-amd-10k", "quick ratio", document_name="AMD_2022_10K.pdf"),
            chunk("amd-2022-10q", "doc-amd-10q", "quarterly liquidity", document_name="AMD_2022Q3_10Q.pdf"),
        ],
        [(1.0, 0.0), (0.9, 0.1), (0.0, 1.0), (0.1, 0.9)],
    )

    assert store.infer_filing_metadata_filter(
        "What was the FY2018-to-FY2019 change in Walmart operating-income margin?"
    ) == {"document_name": "WALMART_2019_10K.pdf"}
    assert store.infer_filing_metadata_filter(
        "Does AMD have a healthy liquidity profile based on its FY2022 quick ratio?"
    ) == {"document_name": "AMD_2022_10K.pdf"}
    store.close()


def test_sparse_query_keeps_meaningful_question_terms() -> None:
    terms = _sparse_query_terms("What is capital expenditure in the cash flow statement?")

    assert "capital" in terms
    assert "expenditure" in terms
    assert "statement" in terms
    assert " OR " in terms


def test_financial_reranking_keeps_statement_headers_and_income_as_evidence() -> None:
    question = "What was the annual net income in millions?"
    statement_row = "Table of Contents Consolidated Statements of Income Net income 11,588"
    unrelated_text = "Table of Contents The board discussed net income matters."

    assert _financial_keyword_relevance(statement_row, question) > _financial_keyword_relevance(
        unrelated_text, question
    )


def test_financial_reranking_matches_singular_question_terms_to_plural_rows() -> None:
    question = "What was the inventory balance?"
    statement_row = "Consolidated Balance Sheets Merchandise inventories 5,409"
    unrelated_text = "The inventory process was reviewed."

    assert _financial_keyword_relevance(statement_row, question) > _financial_keyword_relevance(
        unrelated_text, question
    )


def test_financial_retrieval_expands_standard_statement_aliases() -> None:
    assert "purchases property equipment" in retrieval_query("What was capital expenditure?")
    assert "cost of revenue" in retrieval_query("What was cost of goods sold?")
    assert "merchandise inventory" in retrieval_query("What was year-end inventory?")
    assert "balance sheet total assets" in retrieval_query("What were total assets?")
    assert "current liabilities" in retrieval_query("Calculate the quick ratio")
    assert "accumulated depreciation" in retrieval_query(
        "What was net property plant and equipment?"
    )
    assert "balance sheet" in retrieval_query("What was year-end net PPNE?")


def test_hybrid_retriever_includes_adjacent_chunks_for_split_table_context(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    retriever = HybridRetriever(TestEmbedder(), store)
    source = [
        chunk("before", "doc-a", "operating risk", chunk_index=0),
        chunk("matching", "doc-a", "revenue increased", chunk_index=1),
        chunk("after", "doc-a", "the requested table value", chunk_index=2),
    ]
    retriever.index(source)

    results = retriever.retrieve("revenue query", 1)

    assert [item.chunk.chunk_id for item in results] == ["matching", "before", "after"]
    store.close()


def test_hybrid_search_diversifies_nearby_anchor_chunks(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    store.upsert(
        [
            chunk("first", "doc-a", "revenue operating income", chunk_index=10),
            chunk("near-first", "doc-a", "revenue operating income", chunk_index=11),
            chunk("separate", "doc-a", "revenue operating income", chunk_index=14),
        ],
        [(1.0, 0.0), (0.99, 0.01), (0.8, 0.2)],
    )

    results = store.hybrid_search((1.0, 0.0), "revenue operating income", top_k=2)

    assert [item.chunk.chunk_id for item in results] == ["first", "separate"]
    store.close()


def test_hybrid_search_considers_all_sparse_matches_in_a_scoped_filing(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    store.upsert(
        [
            chunk(f"narrative-{index}", "doc-a", "inventory discussion", chunk_index=index,
                  document_name="COMPANY_2021_10K.pdf")
            for index in range(250)
        ]
        + [
            chunk("statement-row", "doc-a", "Consolidated Balance Sheets Merchandise inventories 5,409",
                  chunk_index=300, document_name="COMPANY_2021_10K.pdf")
        ],
        [(1.0, 0.0)] * 251,
    )

    results = store.hybrid_search(
        (1.0, 0.0),
        "inventory inventories merchandise inventory",
        top_k=1,
        metadata_filter={"document_name": "COMPANY_2021_10K.pdf"},
    )

    assert results[0].chunk.chunk_id == "statement-row"
    store.close()
