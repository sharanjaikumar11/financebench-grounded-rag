"""Deterministic metrics for retrieval, answer, grounding, and citations."""

from __future__ import annotations

import re
from collections.abc import Sequence

from rag_system.evaluation.datasets import EvaluationCase
from rag_system.schemas import GroundedAnswer, RetrievedChunk


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def document_matches(actual: str, expected: str) -> bool:
    return actual.removesuffix(".pdf").casefold() == expected.removesuffix(".pdf").casefold()


def retrieval_hit(case: EvaluationCase, retrieved: Sequence[RetrievedChunk]) -> bool:
    return any(document_matches(item.chunk.document_name, case.expected_document) for item in retrieved)


def answer_correct(case: EvaluationCase, answer: GroundedAnswer) -> bool:
    return not answer.insufficient_context and normalized_text(case.expected_answer) in normalized_text(answer.text)


def grounding_supported(answer: GroundedAnswer, retrieved: Sequence[RetrievedChunk]) -> bool:
    if answer.insufficient_context:
        return True
    available_sources = {
        (item.chunk.document_id, item.chunk.document_name) for item in retrieved
    }
    return bool(answer.citations) and all(
        (citation.document_id, citation.document_name) in available_sources
        for citation in answer.citations
    )


def citation_correct(case: EvaluationCase, answer: GroundedAnswer) -> bool:
    return not answer.insufficient_context and bool(answer.citations) and all(
        document_matches(citation.document_name, case.expected_document)
        for citation in answer.citations
    )
