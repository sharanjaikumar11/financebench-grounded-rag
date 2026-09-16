"""Prompt construction for source-grounded answers."""

from __future__ import annotations

from collections.abc import Mapping

from rag_system.schemas import RetrievedChunk

INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


def grounded_answer_prompt(
    question: str, source_map: Mapping[str, RetrievedChunk]
) -> str:
    """Build a prompt that restricts the model to retrieved evidence."""
    sources = "\n\n".join(
        f"[{label}] document_id={item.chunk.document_id}; "
        f"document_name={item.chunk.document_name}; "
        f"pages={list(item.chunk.page_numbers)}; "
        f"sections={list(item.chunk.section_titles)}\n{item.chunk.text}"
        for label, item in source_map.items()
    )
    return (
        "Answer the question using only the supplied sources. "
        "Do not add facts not supported by them. "
        f"If the sources do not contain enough evidence, return exactly {INSUFFICIENT_CONTEXT}. "
        "Every factual statement in a supported answer must include one or more source labels "
        "in the format [S1].\n\n"
        f"Question: {question}\n\nSources:\n{sources}"
    )
