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
        "Give the direct answer first and keep it concise. Preserve the unit requested in the "
        "question; for a yes/no question, begin with exactly Yes or No. "
        "When a source gives a value in millions and the question asks for billions, divide by "
        "1,000 and round to two decimal places. Do not return INSUFFICIENT_CONTEXT when an "
        "explicit source figure answers the question after this arithmetic. "
        "For a qualitative finance question, make a concise conclusion from the cited financial "
        "figures when those figures provide the requested basis; compare capital spending with "
        "total-company sales when assessing capital intensity. "
        "Every factual statement in a supported answer must include one or more source labels "
        "in the format [S1]. Cite only source labels that directly support that answer.\n\n"
        f"Question: {question}\n\nSources:\n{sources}"
    )
