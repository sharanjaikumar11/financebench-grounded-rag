import pytest

from rag_system.evaluation.reviewed_scoring import apply_review, summarize_review


def row(case_id="a"):
    return {"case_id": case_id, "status": "completed", "citation_correct": True, "abstained": False}


def decision():
    return {
        "case_id": "a",
        "reference_status": "verified",
        "answer_correct": True,
        "reviewer": "test",
        "reference_reason": "source checked",
        "answer_reason": "claim supported",
        "rubric": "test-v1",
    }


def test_unreviewed_rows_never_become_accuracy():
    result = summarize_review(apply_review([row()], []), 1)
    assert result["answer_accuracy"] is None
    assert result["unresolved_count"] == 1
    assert result["citation_location_accuracy"] == 1


def test_pending_cases_are_not_dropped_from_denominator():
    rows = apply_review([row(), row("b")], [decision()])
    report = summarize_review(rows, 2)
    assert report["answer_accuracy"] is None
    assert report["confirmed_correct_count"] == 1
    assert report["expected_case_count"] == 2


def test_completed_reviews_can_be_scored():
    assert summarize_review(apply_review([row()], [decision()]), 1)["answer_accuracy"] == 1


@pytest.mark.parametrize(
    "field,value",
    [("reference_status", "pending"), ("reviewer", ""), ("answer_correct", "true"), ("rubric", "")],
)
def test_incomplete_decisions_rejected(field, value):
    review = decision()
    review[field] = value
    with pytest.raises(ValueError):
        apply_review([row()], [review])


def test_duplicate_unknown_and_abstaining_reviews_rejected():
    with pytest.raises(ValueError):
        apply_review([row()], [decision(), decision()])
    with pytest.raises(ValueError):
        apply_review([row("other")], [decision()])
    case = row()
    case["abstained"] = True
    with pytest.raises(ValueError):
        apply_review([case], [decision()])


def test_provider_errors_prevent_complete_report():
    case = row()
    case["status"] = "provider_or_pipeline_error"
    result = summarize_review([case], 1)
    assert result["answer_accuracy"] is None
    assert result["citation_location_accuracy"] is None
    with pytest.raises(ValueError):
        apply_review([case], [decision()])
