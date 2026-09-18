from rag_system.generation.table_calculations import TableCalculator
from rag_system.schemas import DocumentChunk, RetrievedChunk


def test_table_calculator_converts_source_table_values_to_requested_unit() -> None:
    source = RetrievedChunk(
        DocumentChunk(
            chunk_id="row", document_id="doc", document_name="report.pdf", chunk_index=0,
            text=("(Dollars in millions)\nProperty, plant and equipment - net 8,738 8,866\n"),
            token_count=10, chunking_strategy="fixed_token", page_numbers=(1,), section_titles=("Balance Sheet",),
        ),
        score=1.0,
    )

    evidence = TableCalculator().evidence("What is property plant equipment in USD billions?", {"S1": source})

    assert len(evidence) == 1
    assert evidence[0].source_label == "S1"
    assert evidence[0].values == (8.738, 8.866)
    assert "8.74" in evidence[0].render()


def test_table_calculator_does_not_make_up_a_unit_or_unmatched_rows() -> None:
    source = RetrievedChunk(
        DocumentChunk(
            chunk_id="row", document_id="doc", document_name="report.pdf", chunk_index=0,
            text="Revenue 100\n", token_count=2, chunking_strategy="fixed_token", page_numbers=(1,), section_titles=(),
        ),
        score=1.0,
    )

    assert TableCalculator().evidence("What is revenue in USD millions?", {"S1": source}) == ()
