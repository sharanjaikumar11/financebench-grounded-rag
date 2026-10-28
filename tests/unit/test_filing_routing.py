from rag_system.retrieval.query_metadata import indexed_filing_filter, normalize_fiscal_periods
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.schemas import DocumentChunk
from rag_system.services.query import RAGQueryService


def test_short_years_and_quarter_wording():
    assert (
        normalize_fiscal_periods("FY22 versus FY'21; ratio 22") == "FY2022 versus FY2021; ratio 22"
    )
    assert indexed_filing_filter(
        "In Q2 of FY2024, Atlas profits?", ["ATLAS_2024Q2_10Q.pdf", "ATLAS_2024_10K.pdf"]
    ) == {"document_name": "ATLAS_2024Q2_10Q.pdf"}


def test_company_scope_without_date_keeps_real_filings():
    names = ["ATLAS_2023_10K.pdf", "ATLAS_2024_10K.pdf", "OTHER_2024_10K.pdf"]
    assert indexed_filing_filter("Atlas dividend trend?", names) == {"document_names": names[:2]}
    assert indexed_filing_filter("Atlas FY25 income?", names) == {"document_names": []}


def test_catalog_aliases_and_ambiguity():
    assert indexed_filing_filter("AnB FY24 income?", ["ALPHA_BETA_2024_10K.pdf"]) == {
        "document_name": "ALPHA_BETA_2024_10K.pdf"
    }
    assert (
        indexed_filing_filter(
            "ABC FY24 income?", ["ABCHOLDINGS_2024_10K.pdf", "ABCCORP_2024_10K.pdf"]
        )
        == {}
    )
    assert (
        indexed_filing_filter(
            "Atlas and Other FY24 comparison?", ["ATLAS_2024_10K.pdf", "OTHER_2024_10K.pdf"]
        )
        == {}
    )


def test_earnings_candidates_and_explicit_form():
    names = ["ATLAS_2024_10K.pdf", "ATLAS_2024Q4_EARNINGS.pdf"]
    assert indexed_filing_filter("Atlas FY24 regional earnings?", names) == {
        "document_names": sorted(names)
    }
    assert indexed_filing_filter("Atlas FY24 10-K earnings?", names) == {"document_name": names[0]}


def test_name_set_filter_is_parameterized():
    clauses, values = SQLiteVectorStore._filter_query({"document_names": ["a.pdf", "x' OR 1=1"]})
    assert clauses == ["document_name IN (?,?)"]
    assert values == ["a.pdf", "x' OR 1=1"]


def test_annual_evidence_when_quarter_unavailable():
    names = ["ATLAS_2024_10K.pdf", "ATLAS_2024Q3_10Q.pdf"]
    assert indexed_filing_filter("Atlas Q2 of FY24 dividends?", names) == {
        "document_name": names[0]
    }


def test_case_variants_are_same_company_not_ambiguous():
    names = ["ATLAS_2024_10K.pdf", "Atlas_2025Q2_10Q.pdf"]
    assert indexed_filing_filter("Atlas FY24 revenue?", names) == {"document_name": names[0]}
    assert indexed_filing_filter("Pineapple FY24 revenue?", ["APPLE_2024_10K.pdf"]) == {}


def test_multi_filing_search_reserves_distinct_sources(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCIAL_INTENT_RANKING", "1")
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    try:
        chunks = [
            DocumentChunk(
                f"a{i}",
                "a",
                "ATLAS_2024_10K.pdf",
                i,
                "Dividends paid 90 80 70",
                6,
                "fixed_token",
                (i + 1,),
                (),
            )
            for i in (0, 4, 8)
        ] + [
            DocumentChunk(
                "b",
                "b",
                "ATLAS_2024Q4_EARNINGS.pdf",
                0,
                "Dividends paid 90",
                3,
                "fixed_token",
                (1,),
                (),
            )
        ]
        store.upsert(chunks, [(1.0, 0.0)] * len(chunks))
        result = store.hybrid_search(
            (1.0, 0.0),
            "dividends paid",
            2,
            {"document_names": ["ATLAS_2024_10K.pdf", "ATLAS_2024Q4_EARNINGS.pdf"]},
        )
        assert {hit.chunk.document_id for hit in result} == {"a", "b"}
        assert store.hybrid_search((1.0, 0.0), "dividends", 2, {"document_names": []}) == ()
    finally:
        store.close()


def test_explicit_document_override_removes_inferred_set():
    from types import SimpleNamespace

    captured = []
    retriever = SimpleNamespace(
        vector_store=SimpleNamespace(
            infer_filing_metadata_filter=lambda question: {"document_names": ["a.pdf"]}
        ),
        retrieve=lambda question, top_k, filters: captured.append(filters) or (),
    )
    generator = SimpleNamespace(answer=lambda question, sources: None)
    service = RAGQueryService(None, None, retriever, generator, 3)
    service.answer("Example question", {"document_name": "b.pdf"})
    assert captured == [{"document_name": "b.pdf"}]
