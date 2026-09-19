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
    if answer.insufficient_context:
        return False
    expected = normalized_text(case.expected_answer)
    actual = normalized_text(answer.text)
    if expected in actual:
        return True
    if expected in {"yes", "no"}:
        return bool(re.search(rf"\b{re.escape(expected)}\b", actual))
    expected_value = _financial_value_in_requested_units(case.expected_answer, case.question)
    actual_value = _financial_value_in_requested_units(answer.text, case.question)
    return (
        expected_value is not None
        and actual_value is not None
        and abs(expected_value - actual_value) <= max(0.01, abs(expected_value) * 0.005)
    )


def _financial_value_in_requested_units(value: str, question: str) -> float | None:
    """Normalize dollar figures so equivalent million/billion wording compares fairly."""
    matches = list(
        re.finditer(
            r"(?P<currency>\$)?\s*(?P<amount>[0-9][0-9,]*(?:\.\d+)?)\s*(?P<unit>billion|million|bn|mn)?\b",
            value,
            re.IGNORECASE,
        )
    )
    preferred = [match for match in matches if match.group("currency") or match.group("unit")]
    match = (preferred or matches or [None])[0]
    if match is None:
        return None
    amount = float(match.group("amount").replace(",", ""))
    unit = (match.group("unit") or "").casefold()
    requested = normalized_text(question)
    if "usd billion" in requested or "in billions" in requested:
        return amount * (0.001 if unit in {"million", "mn"} else 1.0)
    if "usd million" in requested or "in millions" in requested:
        return amount * (1000.0 if unit in {"billion", "bn"} else 1.0)
    return amount


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
    return not answer.insufficient_context and bool(answer.citations) and any(
        document_matches(citation.document_name, case.expected_document)
        for citation in answer.citations
    )
