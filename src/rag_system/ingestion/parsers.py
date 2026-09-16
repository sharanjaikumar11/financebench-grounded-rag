"""Format-specific parsers that return normalized, provenance-aware documents."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pymupdf

from rag_system.ingestion.cleaning import normalize_text
from rag_system.schemas import DocumentSegment, ParsedDocument, SourceFormat


class IngestionError(Exception):
    """Base exception for ingestion failures."""


class UnsupportedDocumentError(IngestionError):
    """Raised when a source format is unsupported."""


class EmptyDocumentError(IngestionError):
    """Raised when extraction produces no usable text."""


Parser = Callable[[Path, str, str], ParsedDocument]
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def detect_format(path: Path) -> SourceFormat:
    """Return the supported document format for a source path."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return SourceFormat.PDF
    if suffix == ".txt":
        return SourceFormat.TXT
    if suffix in {".md", ".markdown"}:
        return SourceFormat.MARKDOWN
    raise UnsupportedDocumentError(f"Unsupported document format: {path.suffix}")


def _build_document(
    path: Path,
    document_id: str,
    content_hash: str,
    source_format: SourceFormat,
    segments: list[DocumentSegment],
) -> ParsedDocument:
    if not segments:
        raise EmptyDocumentError(f"No usable text was extracted from: {path.name}")
    return ParsedDocument(
        document_id=document_id,
        document_name=path.name,
        source_path=path,
        source_format=source_format,
        content_hash=content_hash,
        segments=tuple(segments),
    )


def parse_pdf(path: Path, document_id: str, content_hash: str) -> ParsedDocument:
    """Extract one normalized segment per PDF page."""

    segments: list[DocumentSegment] = []
    try:
        with pymupdf.open(path) as pdf:
            for page_index, page in enumerate(pdf):
                text = normalize_text(page.get_text())
                if text:
                    segments.append(
                        DocumentSegment(
                            segment_index=len(segments),
                            page_number=page_index + 1,
                            text=text,
                        )
                    )
    except pymupdf.FileDataError as error:
        raise IngestionError(f"Unable to read PDF: {path.name}") from error
    return _build_document(
        path, document_id, content_hash, SourceFormat.PDF, segments
    )


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise IngestionError(f"Unable to decode text file: {path.name}")


def parse_txt(path: Path, document_id: str, content_hash: str) -> ParsedDocument:
    """Extract a single normalized segment from a text document."""

    text = normalize_text(_read_text_file(path))
    segments = [DocumentSegment(segment_index=0, text=text)] if text else []
    return _build_document(
        path, document_id, content_hash, SourceFormat.TXT, segments
    )


def parse_markdown(path: Path, document_id: str, content_hash: str) -> ParsedDocument:
    """Extract normalized Markdown sections while preserving heading metadata."""

    segments: list[DocumentSegment] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    def flush_section() -> None:
        text = normalize_text("\n".join(current_lines))
        if text:
            segments.append(
                DocumentSegment(
                    segment_index=len(segments),
                    section_title=current_heading,
                    text=text,
                )
            )
        current_lines.clear()

    for line in _read_text_file(path).splitlines():
        heading = _HEADING_PATTERN.match(line)
        if heading:
            flush_section()
            current_heading = heading.group(2)
        else:
            current_lines.append(line)
    flush_section()
    return _build_document(
        path, document_id, content_hash, SourceFormat.MARKDOWN, segments
    )


class ParserRegistry:
    """Dispatch document parsing to the parser registered for its format."""

    def __init__(self) -> None:
        self._parsers: dict[SourceFormat, Parser] = {
            SourceFormat.PDF: parse_pdf,
            SourceFormat.TXT: parse_txt,
            SourceFormat.MARKDOWN: parse_markdown,
        }

    def parse(self, path: Path, document_id: str, content_hash: str) -> ParsedDocument:
        source_format = detect_format(path)
        return self._parsers[source_format](path, document_id, content_hash)
