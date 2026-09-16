"""Core data structures shared by the ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class SourceFormat(StrEnum):
    """Document formats supported by the ingestion pipeline."""

    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "markdown"


@dataclass(frozen=True, slots=True)
class DocumentSegment:
    """A normalized source unit with page or section provenance."""

    segment_index: int
    text: str
    page_number: int | None = None
    section_title: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """A normalized document ready for later chunking and indexing."""

    document_id: str
    document_name: str
    source_path: Path
    source_format: SourceFormat
    content_hash: str
    segments: tuple[DocumentSegment, ...]
