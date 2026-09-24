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
from rag_system.retrieval.query_metadata import filing_metadata_filter
from rag_system.schemas import GroundedAnswer, RetrievedChunk


@dataclass(frozen=True, slots=True)
class EvaluationResponse:
    """The retriever and generator outputs assessed for one case."""

    retrieved: tuple[RetrievedChunk, ...]
    answer: GroundedAnswer


class EvaluatedSystem(Protocol):
    def answer(self, question: str) -> EvaluationResponse: ...


class GroundedEvaluationSystem:
    """Adapter that evaluates retrieved evidence and grounded generation together."""

    def __init__(self, retriever: object, answer_generator: object, top_k: int) -> None:
        if top_k < 1:
            raise ValueError("top_k must be at least one")
        self.retriever = retriever
        self.answer_generator = answer_generator
        self.top_k = top_k

    def answer(self, question: str) -> EvaluationResponse:
        retrieved = self.retriever.retrieve(question, self.top_k, _inferred_filing_filter(self.retriever, question))
        return EvaluationResponse(retrieved, self.answer_generator.answer(question, retrieved))


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    retrieval_hit: bool
    answer_correct: bool
    grounded: bool
    citation_correct: bool
    failures: tuple[str, ...]
    expected_answer: str
    expected_document: str
    generated_answer: str
    retrieved_documents: tuple[str, ...]
    cited_documents: tuple[str, ...]


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


@dataclass(frozen=True, slots=True)
class RetrievalCaseResult:
    """Retrieval-only evidence record for controlled chunking and top-K experiments."""

    case_id: str
    expected_document: str
    expected_pages: tuple[int, ...]
    retrieved_documents: tuple[str, ...]
    retrieved_pages: tuple[tuple[int, ...], ...]
    retrieval_hit: bool


@dataclass(frozen=True, slots=True)
class RetrievalExperimentReport:
    """Comparable retrieval result for one chunking strategy and top-K value."""

    chunking_strategy: str
    top_k: int
    case_count: int
    retrieval_recall: float
    cases: tuple[RetrievalCaseResult, ...]

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
        return CaseResult(
            case_id=case.case_id,
            retrieval_hit=retrieval,
            answer_correct=answer,
            grounded=grounded,
            citation_correct=citation,
            failures=failures,
            expected_answer=case.expected_answer,
            expected_document=case.expected_document,
            generated_answer=response.answer.text,
            retrieved_documents=tuple(item.chunk.document_name for item in response.retrieved),
            cited_documents=tuple(citation.document_name for citation in response.answer.citations),
        )


class RetrievalExperimentRunner:
    """Measure retrieval recall and save source evidence without invoking an answer model."""

    def run(
        self,
        retriever: object,
        cases: Sequence[EvaluationCase],
        chunking_strategy: str,
        top_k: int,
        apply_query_metadata_filter: bool = False,
    ) -> RetrievalExperimentReport:
        if not cases:
            raise ValueError("At least one evaluation case is required")
        results: list[RetrievalCaseResult] = []
        for case in cases:
            metadata_filter: dict[str, object] = {
                "chunking_strategy": chunking_strategy,
            }
            if apply_query_metadata_filter:
                metadata_filter.update(_inferred_filing_filter(retriever, case.question))
            retrieved = retriever.retrieve(
                case.question,
                top_k,
                metadata_filter,
            )[:top_k]
            results.append(
                RetrievalCaseResult(
                    case_id=case.case_id,
                    expected_document=case.expected_document,
                    expected_pages=case.expected_pages,
                    retrieved_documents=tuple(item.chunk.document_name for item in retrieved),
                    retrieved_pages=tuple(item.chunk.page_numbers for item in retrieved),
                    retrieval_hit=retrieval_hit(case, retrieved),
                )
            )
        return RetrievalExperimentReport(
            chunking_strategy=chunking_strategy,
            top_k=top_k,
            case_count=len(results),
            retrieval_recall=sum(result.retrieval_hit for result in results) / len(results),
            cases=tuple(results),
        )


def _inferred_filing_filter(retriever: object, question: str) -> dict[str, object]:
    """Prefer indexed filing metadata; use static parsing only as a fallback."""
    vector_store = getattr(retriever, "vector_store", None)
    infer_from_index = getattr(vector_store, "infer_filing_metadata_filter", None)
    inferred = dict(infer_from_index(question)) if callable(infer_from_index) else {}
    return inferred or dict(filing_metadata_filter(question))
