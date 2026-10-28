import json

import pytest

from rag_system.generation.absence_validation import validate_acquisition_absence
from rag_system.generation.evidence import inspect_evidence_answer
from rag_system.schemas import DocumentChunk, RetrievedChunk


def payload(answer, quote):
    return {
        "answer": answer,
        "period": "FY2024",
        "unit": None,
        "evidence": [{"source_id": "S1", "quote": quote}],
        "calculations": [],
    }


@pytest.mark.parametrize(
    "answer",
    [
        "No acquisitions were reported for FY2024.",
        "The company did not report any acquisitions in FY2024.",
        "In FY2024, there were no acquisitions.",
    ],
)
def test_zero_cash_flow_does_not_prove_absence(answer):
    p = payload(answer, "2024 2023 Acquisitions, net of cash acquired - (350)")
    assert validate_acquisition_absence(p) == "unsupported_acquisition_absence"


def test_explicit_dated_statement_supports_same_year_only():
    p = payload("No acquisitions in FY2024.", "We did not complete any acquisitions in 2024.")
    assert validate_acquisition_absence(p) == "accepted"
    p["answer"] = "No acquisitions in FY2023."
    assert validate_acquisition_absence(p) == "unsupported_acquisition_absence"
    p["answer"] = "No acquisitions in FY2023 and FY2024."
    assert validate_acquisition_absence(p) == "unsupported_acquisition_absence"


def test_material_only_and_plans_do_not_support_unqualified_absence():
    for quote in ["No material acquisitions in FY2024.", "We expect no acquisitions in FY2024."]:
        assert (
            validate_acquisition_absence(payload("No acquisitions in FY2024.", quote))
            == "unsupported_acquisition_absence"
        )


def test_explicit_information_gap_is_not_an_absence_claim():
    p = payload(
        "An acquisition occurred in FY2024; supplied sources contain no information about FY2023 acquisitions.",
        "An acquisition occurred in FY2024.",
    )
    assert validate_acquisition_absence(p) == "accepted"


def test_guard_runs_after_quote_validation_and_is_opt_in(monkeypatch):
    p = payload("No acquisitions in FY2024.", "Acquisitions cash outflow 0")
    source = RetrievedChunk(
        DocumentChunk(
            chunk_id="c",
            document_id="d",
            document_name="example.pdf",
            chunk_index=0,
            text=p["evidence"][0]["quote"],
            token_count=4,
            chunking_strategy="fixed_token",
            page_numbers=(1,),
            section_titles=(),
        ),
        1.0,
    )
    monkeypatch.setenv("ABSENCE_VALIDATION", "0")
    assert inspect_evidence_answer(json.dumps(p), {"S1": source})[1] == "accepted"
    monkeypatch.setenv("ABSENCE_VALIDATION", "1")
    assert (
        inspect_evidence_answer(json.dumps(p), {"S1": source})[1]
        == "unsupported_acquisition_absence"
    )
    p["evidence"][0]["quote"] = "No acquisitions in FY2024."
    assert inspect_evidence_answer(json.dumps(p), {"S1": source})[1] == "quote_not_in_source"
