from pathlib import Path

import pymupdf

from rag_system.chunking.tables import TableAwareChunker, serialize_table_rows
from rag_system.ingestion.parsers import parse_pdf
from rag_system.retrieval.reranking import CrossEncoderReranker
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.schemas import DocumentChunk, RetrievedChunk


def test_table_serialization_keeps_empty_column_and_period_alignment():
    rows = serialize_table_rows([["Assets", None, "123"]], ["Metric", "2024", "2023"])
    assert "Column 2 (2024): [empty]" in rows[0]
    assert "Column 3 (2023): 123" in rows[0]


def test_real_pdf_table_extraction_retains_header_and_page(tmp_path: Path):
    path = tmp_path / "table.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((50, 60), "Balance sheet (USD millions)")
        for y in (80, 110, 140):
            page.draw_line((50, y), (350, y))
        for x in (50, 150, 250, 350):
            page.draw_line((x, 80), (x, 140))
        for x, value in ((60, "Metric"), (160, "2024"), (260, "2023")):
            page.insert_text((x, 100), value)
        for x, value in ((60, "Assets"), (160, "123"), (260, "110")):
            page.insert_text((x, 130), value)
        pdf.save(path)
    document = parse_pdf(path, "test", "hash")
    chunks = TableAwareChunker(200, 40).chunk(document)
    tables = [c for c in chunks if c.section_titles and c.section_titles[0].startswith("Table")]
    assert len(tables) == 2
    assert "(2024): 123" in tables[1].text
    assert "USD millions" in tables[0].text
    assert tables[0].page_numbers == (1,)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert chunks == TableAwareChunker(200, 40).chunk(document)


def candidate(index):
    return RetrievedChunk(
        DocumentChunk(
            str(index),
            "doc",
            "test.pdf",
            index,
            f"Evidence {index}",
            2,
            "fixed_token",
            (index + 1,),
            (),
        ),
        0.5,
    )


def test_cross_encoder_reorders_candidates_without_losing_provenance():
    class Model:
        def predict(self, pairs, **kwargs):
            assert pairs == [("Question", "Evidence 0"), ("Question", "Evidence 1")]
            return [0.1, 0.9]

    reranker = CrossEncoderReranker("local-model")
    reranker._model = Model()
    result = reranker.rerank("Question", (candidate(0), candidate(1)), 1)
    assert result[0].chunk == candidate(1).chunk


def test_hybrid_reranks_wide_pool_before_neighbor_expansion():
    class Embedder:
        def embed(self, texts):
            return [(1.0,)]

    class Store:
        def hybrid_search(self, vector, query, top_k, metadata, original_query=None):
            assert original_query == "Question"
            assert top_k == 30
            assert metadata == {"document_name": "test.pdf"}
            return (candidate(0), candidate(1))

        def expand_with_neighbors(self, anchors):
            assert anchors == (candidate(1),)
            return anchors

    class Ranker:
        def rerank(self, query, candidates, top_k):
            assert top_k == 1
            return (candidates[1],)

    result = HybridRetriever(Embedder(), Store(), Ranker(), 30).retrieve(
        "Question", 1, {"document_name": "test.pdf"}
    )
    assert result == (candidate(1),)
