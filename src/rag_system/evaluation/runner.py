"""Evaluation execution and failure recording."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Protocol

from rag_system.evaluation.datasets import EvaluationCase
from rag_system.evaluation.metrics import (
    answer_correct,
    citation_correct,
    grounding_supported,
    retrieval_hit,
)
from rag_system.schemas import GroundedAnswer, RetrievedChunk


@dataclass(frozen=True, slots=True)
class EvaluationResponse:
    """The retriever and generator outputs assessed for one case."""

    retrieved: tuple[RetrievedChunk, ...]
    answer: GroundedAnswer


class EvaluatedSystem(Protocol):
    def answer(self, question: str) -> EvaluationResponse: ...


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    retrieval_hit: bool
    answer_correct: bool
    grounded: bool
    citation_correct: bool
    failures: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    case_count: int
    retrieval_recall: float
    answer_accuracy: float
    grounding_rate: float
    citation_accuracy: float
    failures: tuple[CaseResult, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class EvaluationRunner:
    """Run all cases and aggregate client-required quality measures."""

    def run(self, system: EvaluatedSystem, cases: Sequence[EvaluationCase]) -> EvaluationReport:
        if not cases:
            raise ValueError("At least one evaluation case is required")
        results = tuple(self._evaluate_case(case, system.answer(case.question)) for case in cases)
        total = len(results)
        return EvaluationReport(
            case_count=total,
            retrieval_recall=sum(result.retrieval_hit for result in results) / total,
            answer_accuracy=sum(result.answer_correct for result in results) / total,
            grounding_rate=sum(result.grounded for result in results) / total,
            citation_accuracy=sum(result.citation_correct for result in results) / total,
            failures=tuple(result for result in results if result.failures),
        )

    @staticmethod
    def _evaluate_case(case: EvaluationCase, response: EvaluationResponse) -> CaseResult:
        retrieval = retrieval_hit(case, response.retrieved)
        answer = answer_correct(case, response.answer)
        grounded = grounding_supported(response.answer, response.retrieved)
        citation = citation_correct(case, response.answer)
        failures = tuple(
            label
            for label, passed in (
                ("retrieval_miss", retrieval),
                ("incorrect_answer", answer),
                ("unsupported_answer", grounded),
                ("incorrect_citation", citation),
            )
            if not passed
        )
        return CaseResult(case.case_id, retrieval, answer, grounded, citation, failures)
