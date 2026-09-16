"""Repeatable indexing for supported source files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag_system.ingestion.parsers import detect_format
from rag_system.ingestion.parsers import UnsupportedDocumentError
from rag_system.services.query import RAGQueryService


@dataclass(frozen=True, slots=True)
class IndexRun:
    """Summary of one repeatable directory-indexing run."""

    indexed: int
    duplicates: int
    failed: tuple[str, ...]


def discover_supported_documents(source_directory: Path) -> tuple[Path, ...]:
    """Find PDF, TXT, and Markdown sources in a deterministic order."""
    if not source_directory.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source_directory}")
    supported: list[Path] = []
    for path in sorted(source_directory.rglob("*")):
        if not path.is_file():
            continue
        try:
            detect_format(path)
        except UnsupportedDocumentError:
            continue
        supported.append(path)
    return tuple(supported)


def index_directory(service: RAGQueryService, source_directory: Path) -> IndexRun:
    """Index all supported files and retain any individual failure for review."""
    indexed = 0
    duplicates = 0
    failed: list[str] = []
    for path in discover_supported_documents(source_directory):
        try:
            result = service.index_document(path)
        except Exception as error:
            failed.append(f"{path.name}: {error}")
            continue
        if result.status == "indexed":
            indexed += 1
        else:
            duplicates += 1
    return IndexRun(indexed=indexed, duplicates=duplicates, failed=tuple(failed))
