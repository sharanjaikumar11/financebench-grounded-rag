import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def module(monkeypatch):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    return runpy.run_path(str(scripts / "run_50_generation_collection.py"))


def test_subset_keeps_original_cohorts_and_deduplicates_ids(module):
    cases = [SimpleNamespace(case_id=key) for key in ("a", "b", "c", "d")]
    selected, originals = module["select_cases"](cases, 2, ["d", "b", "b"])
    assert [c.case_id for c in selected] == ["b", "d"]
    assert originals == {"a", "b"}
    assert module["select_cases"](cases, 2, [])[0] == cases
    with pytest.raises(ValueError, match="Unknown"):
        module["select_cases"](cases, 2, ["missing"])


def test_partial_targeted_summary_keeps_selected_denominators(module):
    cases = [SimpleNamespace(case_id=key) for key in ("b", "d", "e")]
    rows = [
        {"case_id": "d", "status": "completed", "citation_correct": True, "answer_correct": None}
    ]
    result = module["collection_summary"](rows, cases, {"a", "b"})
    assert result["original"]["expected_case_count"] == 1
    assert result["original"]["collected_case_count"] == 0
    assert result["additions"]["expected_case_count"] == 2
    assert result["additions"]["collected_case_count"] == 1
    assert result["combined"]["expected_case_count"] == 3
    assert result["combined"]["answer_accuracy"] is None


def test_target_without_original_cases_has_no_empty_group_accuracy(module):
    cases = [SimpleNamespace(case_id="added")]
    rows = [
        {
            "case_id": "added",
            "status": "completed",
            "citation_correct": True,
            "answer_correct": None,
        }
    ]
    result = module["collection_summary"](rows, cases, {"original"})
    assert result["original"]["expected_case_count"] == 0
    assert result["original"]["answer_accuracy"] is None
    assert result["original"]["citation_location_accuracy"] is None
    assert result["combined"]["citation_location_accuracy"] == 1.0
