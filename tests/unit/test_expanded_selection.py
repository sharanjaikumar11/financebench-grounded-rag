import runpy
from pathlib import Path

import pytest

SELECT = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/prepare_expanded_evaluation.py")
)["select_additions"]


def test_selection_independent_of_input_order_and_answers():
    records = [
        {
            "financebench_id": str(i),
            "question": f"Question {i}?",
            "company": chr(65 + i % 3),
            "answer": "unscored",
        }
        for i in range(12)
    ]
    first = SELECT(records, [], 6)
    reversed_records = [{**r, "answer": "different"} for r in reversed(records)]
    assert [r["financebench_id"] for r in first] == [
        r["financebench_id"] for r in SELECT(reversed_records, [], 6)
    ]
    assert [r["company"] for r in first] == ["A", "B", "C", "A", "B", "C"]


def test_duplicate_questions_do_not_stop_selection_early():
    records = [{"financebench_id": str(i), "question": "Same?", "company": "A"} for i in range(20)]
    records.append({"financebench_id": "unique", "question": "Different?", "company": "A"})
    selected = SELECT(records, [], 2)
    assert {r["question"] for r in selected} == {"Same?", "Different?"}
    with pytest.raises(ValueError, match="Not enough"):
        SELECT(records, [], 3)
