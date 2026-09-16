"""Citation extraction for model responses grounded in retrieved chunks."""

from __future__ import annotations

import re
from collections.abc import Mapping

from rag_system.schemas import Citation, RetrievedChunk

_SOURCE_LABEL = re.compile(r"\[S(\d+)]")


def build_source_map(chunks: tuple[RetrievedChunk, ...]) -> dict[str, RetrievedChunk]:
    """Assign stable source labels in retrieval rank order."""
    return {f"S{index}": chunk for index, chunk in enumerate(chunks, start=1)}


def citations_from_answer(
    answer_text: str, source_map: Mapping[str, RetrievedChunk]
) -> tuple[Citation, ...]:
    """Return only valid, explicitly referenced source citations."""
    citations: list[Citation] = []
    seen: set[str] = set()
    for match in _SOURCE_LABEL.finditer(answer_text):
        label = f"S{match.group(1)}"
        if label in seen or label not in source_map:
            continue
        seen.add(label)
        chunk = source_map[label].chunk
        citations.append(
            Citation(
                source_label=label,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                page_numbers=chunk.page_numbers,
                section_titles=chunk.section_titles,
            )
        )
    return tuple(citations)
