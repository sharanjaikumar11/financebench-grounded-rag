"""Repeatable ingestion orchestration with duplicate detection."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rag_system.ingestion.parsers import ParserRegistry
from rag_system.schemas import ParsedDocument


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Outcome of one ingestion attempt."""

    status: str
    document: ParsedDocument | None


class DocumentRegistry:
    """SQLite registry that prevents identical source content from re-indexing."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    content_hash TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    source_format TEXT NOT NULL,
                    segment_count INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                )
                """
            )

    def contains(self, content_hash: str) -> bool:
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM documents WHERE content_hash = ?", (content_hash,)
            ).fetchone()
        return row is not None

    def register(self, document: ParsedDocument) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    content_hash, document_id, document_name, source_format,
                    segment_count, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document.content_hash,
                    document.document_id,
                    document.document_name,
                    document.source_format.value,
                    len(document.segments),
                    datetime.now(UTC).isoformat(),
                ),
            )


def file_hash(path: Path) -> str:
    """Return a stable SHA-256 digest for source-content duplicate detection."""

    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class DocumentIngestor:
    """Parse and register supported source documents exactly once per content hash."""

    def __init__(self, registry: DocumentRegistry, parsers: ParserRegistry | None = None) -> None:
        self.registry = registry
        self.parsers = parsers or ParserRegistry()

    def ingest(
        self, source_path: Path, parse_if_duplicate: bool = False
    ) -> IngestionResult:
        source_path = source_path.resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"Source document does not exist: {source_path}")

        content_hash = file_hash(source_path)
        if self.registry.contains(content_hash):
            if parse_if_duplicate:
                document_id = f"doc_{content_hash[:16]}"
                document = self.parsers.parse(source_path, document_id, content_hash)
                return IngestionResult(status="duplicate", document=document)
            return IngestionResult(status="duplicate", document=None)

        document_id = f"doc_{content_hash[:16]}"
        document = self.parsers.parse(source_path, document_id, content_hash)
        self.registry.register(document)
        return IngestionResult(status="ingested", document=document)
