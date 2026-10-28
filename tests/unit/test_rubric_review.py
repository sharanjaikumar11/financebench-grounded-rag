import pytest

from scripts.prepare_rubric_review import build_ledger, suggested_rubric


def test_rubric_triage_handles_signed_ratio_percentage_and_verdict():
    assert suggested_rubric("ROA?", "-0.02") == "signed_numeric_with_explicit_unit_and_rounding"
    assert suggested_rubric("Change?", "0.2%") == "percentage_or_percentage_point_change"
    assert (
        suggested_rubric("Increased?", "No, decreased by 20")
        == "verdict_plus_required_supporting_claims"
    )


def test_review_ledger_does_not_promote_cases_or_change_inputs():
    original = [
        {"case_id": "a", "question": "q", "expected_answer": "1", "expected_document": "d.pdf"}
    ]
    rows = build_ledger(original, original, {"cases": []})
    assert not rows[0]["approved_for_new_scoring"]
    assert "validation_status" not in original[0]
    with pytest.raises(ValueError, match="Original cases changed"):
        build_ledger([], original, {"cases": []})
