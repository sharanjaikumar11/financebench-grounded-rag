import hashlib
import json
import runpy
from pathlib import Path

import pytest

MODULE = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/run_audited_retrieval.py")
)


def fixture_files(tmp_path):
    baseline = {
        "case_id": "old",
        "question": "Old?",
        "expected_answer": "1",
        "expected_document": "a.pdf",
    }
    addition = {
        **baseline,
        "case_id": "new",
        "question": "New?",
        "validation_status": "pending_source_review",
    }
    draft, original, audit = [
        tmp_path / name for name in ("draft.json", "original.json", "audit.json")
    ]
    draft.write_text(json.dumps([baseline, addition]))
    original.write_text(json.dumps([baseline]))
    report = {
        "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest(),
        "cases": [
            {
                "case_id": "new",
                "page_checks": [
                    {
                        "document": "a.pdf",
                        "candidates": [{"physical_page": 3, "evidence_overlap": 1.0}],
                    }
                ],
            }
        ],
    }
    audit.write_text(json.dumps(report))
    return draft, audit, original


def test_source_audited_draft_is_retrieval_only(tmp_path):
    from rag_system.evaluation.datasets import load_evaluation_cases

    paths = fixture_files(tmp_path)
    cases, count = MODULE["audited_cases"](*paths)
    assert count == 1
    assert cases[1].expected_pages == (3,)
    with pytest.raises(ValueError, match="source review"):
        load_evaluation_cases(paths[0])


def test_stale_audit_rejected(tmp_path):
    paths = fixture_files(tmp_path)
    paths[0].write_text(paths[0].read_text() + " ")
    with pytest.raises(ValueError, match="stale"):
        MODULE["audited_cases"](*paths)


def test_ambiguous_page_rejected(tmp_path):
    paths = fixture_files(tmp_path)
    report = json.loads(paths[1].read_text())
    report["cases"][0]["page_checks"][0]["candidates"].append(
        {"physical_page": 4, "evidence_overlap": 1.0}
    )
    paths[1].write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Unresolved"):
        MODULE["audited_cases"](*paths)


def test_empty_group_and_unlabelled_pages():
    assert MODULE["summarize"]([])["filing_recall"] is None
    result = MODULE["summarize"]([{"filing_hit": True, "page_hit": None, "all_pages_hit": None}])
    assert result["filing_recall"] == 1.0
    assert result["any_evidence_page_recall"] is None
