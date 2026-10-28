import json
from pathlib import Path

import pytest

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.provenance import run_metadata


@pytest.mark.parametrize("status", ["pending_source_review", "source_reviewed", "pending_rubric"])
def test_draft_cases_are_not_scored(tmp_path, status):
    path = tmp_path / "draft.json"
    path.write_text(json.dumps([{"validation_status": status}]))
    with pytest.raises(ValueError, match="source review"):
        load_evaluation_cases(path)


def test_metadata_records_configuration_without_secrets(tmp_path, monkeypatch):
    cases = tmp_path / "cases.json"
    cases.write_text("[]")
    index = tmp_path / "vectors.sqlite3"
    index.write_bytes(b"test")
    monkeypatch.setenv("GEMINI_API_KEY", "private-key-never-export")
    monkeypatch.setenv("STATEMENT_AWARE_RANKING", "1")
    report = run_metadata(cases, index, "hybrid", 3)
    assert report["settings"]["STATEMENT_AWARE_RANKING"] == "1"
    assert "private-key-never-export" not in json.dumps(report)
    assert len(report["dataset_sha256"]) == 64
    cases.write_text("[{}]")
    assert run_metadata(cases, index, "hybrid", 3)["dataset_sha256"] != report["dataset_sha256"]
    assert set(report["prompt_sha256"]) == {
        "prompts.py",
        "evidence.py",
        "calculations.py",
        "comparisons.py",
        "metric_identity.py",
        "period_validation.py",
        "absence_validation.py",
    }
    assert report["settings"]["CALCULATION_VALIDATION"] == "0"


def test_original_cases_still_load():
    assert len(load_evaluation_cases(Path("evaluation/cases.json"))) == 11
