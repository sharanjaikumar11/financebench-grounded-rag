import copy
import json

import pytest

from rag_system.generation.comparisons import comparison_operation, render_comparison
from rag_system.generation.evidence import inspect_evidence_answer
from rag_system.schemas import DocumentChunk, RetrievedChunk


def payload():
    return {
        "answer": "{{winner}} had the highest income.",
        "period": "2025",
        "unit": "million",
        "calculations": [],
        "evidence": [{"source_id": "S1", "quote": "Retail 30 Markets 45 Corporate (5)"}],
        "comparison": {
            "operation": "max",
            "candidates": [
                {
                    "label": label,
                    "value": value,
                    "label_evidence_index": 0,
                    "value_evidence_index": 0,
                    "period": "2025",
                    "unit": "million",
                    "metric": "income",
                }
                for label, value in [("Retail", "30"), ("Markets", "45"), ("Corporate", "-5")]
            ],
        },
    }


def test_extrema_are_computed_from_signed_candidates():
    p = payload()
    assert render_comparison(p, "max") == ("Markets had the highest income.", "accepted")
    p["comparison"]["operation"] = "min"
    p["answer"] = "{{winner}} had the lowest income."
    assert render_comparison(p, "min")[0] == "Corporate had the lowest income."


@pytest.mark.parametrize(
    "change",
    [
        {"value": "99"},
        {"label": "Invented"},
        {"value": "5"},
    ],
)
def test_unquoted_or_wrong_sign_candidates_rejected(change):
    p = payload()
    p["comparison"]["candidates"][2].update(change)
    assert render_comparison(p, "max")[1] == "comparison_candidate_not_in_evidence"


@pytest.mark.parametrize("field", ["period", "unit", "metric"])
def test_incompatible_candidates_rejected(field):
    p = payload()
    p["comparison"]["candidates"][0][field] = "other"
    assert render_comparison(p, "max")[1] == "comparison_incompatible_candidates"


def test_duplicates_ties_and_preselected_winner_rejected():
    p = payload()
    p["comparison"]["candidates"].append(copy.deepcopy(p["comparison"]["candidates"][0]))
    assert render_comparison(p, "max")[1] == "invalid_comparison"
    p = payload()
    p["comparison"]["candidates"][0]["value"] = "45"
    assert render_comparison(p, "max")[1] == "comparison_tie"
    p = payload()
    p["answer"] = "Retail had the highest income."
    assert render_comparison(p, "max")[1] == "invalid_comparison"


def test_opt_in_integrates_with_calculations_and_quote_checks(monkeypatch):
    monkeypatch.setenv("COMPARISON_VALIDATION", "1")
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    p = payload()
    sources = {
        "S1": RetrievedChunk(
            DocumentChunk(
                chunk_id="c",
                document_id="d",
                document_name="example.pdf",
                chunk_index=0,
                text=p["evidence"][0]["quote"],
                token_count=6,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            score=1.0,
        )
    }
    answer, status = inspect_evidence_answer(json.dumps(p), sources, "Which has highest income?")
    assert status == "accepted"
    assert answer.text == "Markets had the highest income. [S1]"
    p.pop("calculations")
    assert inspect_evidence_answer(json.dumps(p), sources, "Highest income?")[1] == "accepted"
    p["answer"] = "{{winner}} had the highest income of 45."
    assert (
        inspect_evidence_answer(json.dumps(p), sources, "Highest income?")[1]
        == "invalid_calculations"
    )
    p["answer"] = "{{winner}} had the highest income, calculated as {{amount}}."
    assert (
        inspect_evidence_answer(json.dumps(p), sources, "Highest income?")[1]
        == "invalid_calculations"
    )
    p["answer"] = "{{winner}} had the highest income."
    p["calculations"] = None
    assert (
        inspect_evidence_answer(json.dumps(p), sources, "Highest income?")[1]
        == "invalid_calculations"
    )
    p["evidence"][0]["quote"] = "Invented table"
    assert (
        inspect_evidence_answer(json.dumps(p), sources, "Highest income?")[1]
        == "quote_not_in_source"
    )


def test_ambiguous_direction_not_guessed():
    assert comparison_operation("highest income") == "max"
    assert comparison_operation("lowest cost") == "min"
    assert comparison_operation("most or least cash") is None
    assert comparison_operation("total assets") is None


def test_missing_calculations_gate_allows_dates_not_arithmetic():
    from rag_system.generation.comparisons import comparison_only_template

    assert comparison_only_template(
        "In Q2 2025, {{winner}} had the highest income.", "Highest income in Q2 2025?"
    )
    assert not comparison_only_template("{{winner}} had a margin of 25%.", "Highest margin?")
    assert not comparison_only_template("{{winner}} exceeded peers by {{difference}}.", "Highest?")
    assert not comparison_only_template("{{winner}} had income of 300.", "Highest income?")
