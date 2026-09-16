"""Loading for the small FinanceBench-based evaluation set."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    """Question, expected answer, and expected source document for evaluation."""

    case_id: str
    question: str
    expected_answer: str
    expected_document: str


def load_evaluation_cases(path: Path) -> tuple[EvaluationCase, ...]:
    """Load and minimally validate committed evaluation cases."""
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Evaluation cases must be a non-empty JSON list")
    cases = tuple(
        EvaluationCase(
            case_id=item["case_id"],
            question=item["question"],
            expected_answer=item["expected_answer"],
            expected_document=item["expected_document"],
        )
        for item in raw_cases
    )
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("Evaluation case IDs must be unique")
    return cases
