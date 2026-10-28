from rag_system.retrieval.financial_intent import (
    concept_phrases,
    intent_relevance,
    numeric_row_phrases,
    operand_coverage_order,
    transaction_coverage_order,
)
from rag_system.retrieval.retriever import retrieval_query
from rag_system.retrieval.vector_store import _financial_keyword_relevance
from rag_system.schemas import DocumentChunk, RetrievedChunk


def test_standard_accounting_abbreviations(monkeypatch):
    monkeypatch.setenv("FINANCIAL_INTENT_RANKING", "1")
    assert "cost of revenue" in retrieval_query("Example FY24 COGS?")
    assert "trade receivables" in retrieval_query("Example net AR?")
    assert "litigation" in concept_phrases("Any ongoing legal battles?")


def test_numeric_rows_are_not_just_concept_mentions():
    assert numeric_row_phrases("Operating income (600) 450", "Operating income?")
    assert not numeric_row_phrases(
        "Operating income increased during the year", "Operating income?"
    )
    assert not numeric_row_phrases("Assets 600", "Operating income?")


def test_target_evidence_beats_audit_prose(monkeypatch):
    monkeypatch.setenv("FINANCIAL_INTENT_RANKING", "1")
    query = "Year over year operating income from income statement?"
    row = "Consolidated statements of income Operating income 900 800 Revenue 5000 4000"
    audit = "We have audited the consolidated balance sheets and statements of income and cash flows for the years 2024 and 2023."
    assert _financial_keyword_relevance(row, query) > _financial_keyword_relevance(audit, query)


def test_narrative_query_not_forced_to_numeric_statements(monkeypatch):
    monkeypatch.setenv("FINANCIAL_INTENT_RANKING", "1")
    query = "What acquisitions were completed?"
    assert _financial_keyword_relevance(
        "Business combinations: acquired Example Ltd.", query
    ) > _financial_keyword_relevance(
        "Consolidated balance sheets assets 900 800 cash 700 600", query
    )


def test_registration_and_litigation_evidence():
    assert (
        intent_relevance(
            "Securities registered under Section 12 Title of each class Trading symbol",
            "Which debt securities are registered on an exchange?",
        )
        > 0.8
    )
    assert (
        intent_relevance("Legal proceedings: ongoing litigation and lawsuits", "Any legal battles?")
        > 0.8
    )


def test_operand_coverage_reserves_distinct_rows_not_repeated_policy_mentions():
    def item(index, text):
        return RetrievedChunk(
            DocumentChunk(
                chunk_id=str(index),
                document_id="d",
                document_name="sample.pdf",
                chunk_index=index,
                text=text,
                token_count=20,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            1.0,
        )

    policy = item(0, "Total assets and net income are discussed in our accounting policy.")
    parent = item(1, "Parent Guarantor Net income 900 700")
    assets = item(2, "Total assets 800 600")
    income = item(3, "NET INCOME (LOSS) (40) 20")
    candidates = [policy, parent, income, assets]
    result = operand_coverage_order(candidates, "return on assets", 2)
    assert result[:2] == [assets, income]
    assert len(result) == len(candidates)
    assert operand_coverage_order(candidates, "CEO experience", 2) == candidates


def test_capex_and_cogs_aliases_preserve_accounting_labels():
    assert "capital expenditures" in concept_phrases("capex as a percent of revenue")
    assert "cost of products sold" in concept_phrases("inventory turnover")
    assert numeric_row_phrases("Net income (loss) (20) 35", "net income")


def test_transaction_fallback_preserves_already_covered_ranking():
    def item(i, text):
        return RetrievedChunk(
            DocumentChunk(
                chunk_id=str(i),
                document_id="d",
                document_name="sample.pdf",
                chunk_index=i,
                text=text,
                token_count=20,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            1.0,
        )

    policy = item(
        0, "Contingent purchase consideration liabilities from a subsidiary acquired in May 2017"
    )
    transaction = item(
        1, "In May 2024 we acquired Example Ltd; purchase consideration was $80 million"
    )
    candidates = [policy, transaction]
    assert transaction_coverage_order(candidates, "What acquisitions?", 1)[0] == transaction
    assert transaction_coverage_order(candidates, "What acquisitions?", 2) == candidates


def test_generation_keeps_distinct_operands_with_fixed_budget(monkeypatch):
    from rag_system.generation.answering import _generation_evidence_sources

    monkeypatch.setenv("OPERAND_COVERAGE", "1")
    monkeypatch.setenv("NUMERIC_ROW_COVERAGE", "1")
    texts = ["Inventory inventory turnover accounting policy and cost of goods sold"] * 10
    texts += ["Inventory 80 70", "Cost of products sold 400 380"]
    sources = tuple(
        RetrievedChunk(
            DocumentChunk(
                chunk_id=str(i),
                document_id="d",
                document_name="sample.pdf",
                chunk_index=i * 4,
                text=text,
                token_count=20,
                chunking_strategy="fixed_token",
                page_numbers=(i + 1,),
                section_titles=(),
            ),
            1.0,
        )
        for i, text in enumerate(texts)
    )
    selected = _generation_evidence_sources("Inventory turnover?", sources, maximum_sources=3)
    assert len(selected) == 3
    assert sources[-1] in selected and sources[-2] in selected
    assert len(_generation_evidence_sources("Inventory turnover?", sources, maximum_sources=1)) == 1


def test_operand_selection_prefers_main_statement_over_affiliate_note():
    def item(index, text, doc="d"):
        return RetrievedChunk(
            DocumentChunk(
                chunk_id=f"{doc}-{index}",
                document_id=doc,
                document_name=f"{doc}.pdf",
                chunk_index=index,
                text=text,
                token_count=20,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            1.0,
        )

    affiliate = item(30, "Equity method affiliates Net income (loss) (25) 45")
    header = item(10, "Consolidated Statements of Operations Years ended December 31 2024 2023")
    row = item(11, "Net income (loss) (80) 70")
    candidates = [affiliate, row, header]
    assert operand_coverage_order(candidates, "Return on assets", 2)[0] == row
    other_header = item(29, header.chunk.text, "other")
    assert (
        operand_coverage_order([affiliate, row, other_header], "Return on assets", 2)[0]
        == affiliate
    )


def test_operand_context_keeps_header_and_split_row_continuation(monkeypatch):
    from rag_system.generation.answering import _generation_evidence_sources

    monkeypatch.setenv("OPERAND_COVERAGE", "1")
    monkeypatch.setenv("CONTEXT_DIVERSITY_RANKING", "1")
    contents = [
        (10, "Consolidated Balance Sheets in millions 2024 2023"),
        (11, "Total assets 800"),
        (12, "Total assets 800 700"),
        (20, "Consolidated Statements of Operations Years ended 2024 2023"),
        (21, "Net income (loss) (30) 20"),
    ]
    contents += [
        (40 + i * 4, "Total assets net income discussion accounting policy") for i in range(10)
    ]
    sources = tuple(
        RetrievedChunk(
            DocumentChunk(
                chunk_id=str(i),
                document_id="d",
                document_name="sample.pdf",
                chunk_index=i,
                text=text,
                token_count=20,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            1.0,
        )
        for i, text in contents
    )
    selected = _generation_evidence_sources("Return on assets", sources)
    assert len(selected) <= 9
    assert {10, 11, 12, 20, 21} <= {s.chunk.chunk_index for s in selected}


def test_acquisition_context_keeps_event_continuations(monkeypatch):
    from rag_system.generation.answering import _generation_evidence_sources

    monkeypatch.setenv("OPERAND_COVERAGE", "1")
    monkeypatch.setenv("CONTEXT_DIVERSITY_RANKING", "1")
    contents = [
        (10, "On May 1, 2024, the Company completed the acquisition of Example A."),
        (11, "Another acquired operation was Example B."),
        (12, "The third transaction was Example C."),
    ]
    contents += [
        (40 + i * 4, "Acquisitions acquired business combinations non GAAP reconciliation")
        for i in range(12)
    ]
    sources = tuple(
        RetrievedChunk(
            DocumentChunk(
                chunk_id=str(i),
                document_id="d",
                document_name="sample.pdf",
                chunk_index=i,
                text=text,
                token_count=20,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            1.0,
        )
        for i, text in contents
    )
    selected = _generation_evidence_sources("What acquisitions were completed?", sources)
    assert len(selected) <= 9
    assert {10, 11, 12} <= {s.chunk.chunk_index for s in selected}
