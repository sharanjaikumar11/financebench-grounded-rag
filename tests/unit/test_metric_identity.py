import json

import pytest

from rag_system.generation.evidence import inspect_evidence_answer
from rag_system.generation.metric_identity import (
    requests_shareholder_income,
    validate_metric_identity,
)
from rag_system.schemas import DocumentChunk, RetrievedChunk

QUESTION = "Dividend payout ratio using net income attributable to shareholders?"


def payload(metric="net income attributable to shareholders", quote=None):
    quote = quote or "Net income attributable to shareholders 90"
    return {
        "answer": "The ratio is {{ratio}}.",
        "period": "2025",
        "unit": "ratio",
        "evidence": [
            {"source_id": "S1", "quote": quote},
            {"source_id": "S1", "quote": "Dividends (45)"},
        ],
        "calculations": [
            {
                "id": "ratio",
                "expression": "-dividends/income",
                "decimal_places": 2,
                "operands": [
                    {
                        "name": "income",
                        "value": "90",
                        "evidence_index": 0,
                        "metric": metric,
                        "period": "2025",
                        "unit": "million",
                    },
                    {
                        "name": "dividends",
                        "value": "-45",
                        "evidence_index": 1,
                        "metric": "cash dividends",
                        "period": "2025",
                        "unit": "million",
                    },
                ],
            }
        ],
    }


@pytest.mark.parametrize("owner", ["shareholders", "shareowners", "common stockholders"])
def test_supported_attribution(owner):
    metric = "net income attributable to " + owner
    assert requests_shareholder_income("Ratio using " + metric + "?")
    assert validate_metric_identity(payload(metric, metric + " 90"), QUESTION) == "accepted"


def test_consolidated_and_noncontrolling_are_not_substitutes():
    for metric in [
        "consolidated net income",
        "net income",
        "net income attributable to noncontrolling interests",
    ]:
        assert validate_metric_identity(payload(metric), QUESTION) == "income_attribution_mismatch"


def test_relabelling_operand_does_not_change_its_evidence():
    p = payload(quote="Consolidated net income 90")
    assert validate_metric_identity(p, QUESTION) == "income_attribution_not_in_evidence"


def test_other_questions_and_direct_lookups_remain_out_of_scope():
    assert not requests_shareholder_income("What is consolidated net income?")
    assert validate_metric_identity(payload("consolidated net income"), "Net income?") == "accepted"
    p = payload()
    p["calculations"] = []
    assert validate_metric_identity(p, QUESTION) == "accepted"


def test_integration_rejects_wrong_metric_even_with_correct_arithmetic(monkeypatch):
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    monkeypatch.setenv("METRIC_IDENTITY_VALIDATION", "1")
    p = payload("consolidated net income", "Consolidated net income 90")
    sources = {
        "S1": RetrievedChunk(
            DocumentChunk(
                chunk_id="c",
                document_id="d",
                document_name="sample.pdf",
                chunk_index=0,
                text="Consolidated net income 90 Dividends (45)",
                token_count=7,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            score=1.0,
        )
    }
    assert (
        inspect_evidence_answer(json.dumps(p), sources, QUESTION)[1]
        == "income_attribution_mismatch"
    )
    monkeypatch.setenv("METRIC_IDENTITY_VALIDATION", "0")
    answer, status = inspect_evidence_answer(json.dumps(p), sources, QUESTION)
    assert status == "accepted"
    assert answer.text == "The ratio is 0.50. [S1]"
