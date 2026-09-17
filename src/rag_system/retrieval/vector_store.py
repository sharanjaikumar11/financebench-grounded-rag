"""SQLite-backed persistent vector store for dense chunk retrieval."""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Mapping, Sequence
from pathlib import Path

from rag_system.schemas import DocumentChunk, RetrievedChunk


class VectorStoreError(RuntimeError):
    """Raised when vectors cannot be written or searched safely."""


class SQLiteVectorStore:
    """Persist vectors and chunk provenance; rank using cosine similarity."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                chunking_strategy TEXT NOT NULL,
                page_numbers TEXT NOT NULL,
                section_titles TEXT NOT NULL,
                embedding TEXT NOT NULL,
                embedding_dimension INTEGER NOT NULL
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)"
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def has_complete_document(
        self, document_id: str, chunking_strategy: str, expected_chunk_count: int
    ) -> bool:
        """Return whether all chunks for one deterministic indexing configuration exist."""
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS chunk_count
            FROM chunks
            WHERE document_id = ? AND chunking_strategy = ?
            """,
            (document_id, chunking_strategy),
        ).fetchone()
        return row["chunk_count"] == expected_chunk_count

    def upsert(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Each chunk must have exactly one embedding")
        if not chunks:
            return

        dimension = len(embeddings[0])
        if dimension == 0 or any(len(vector) != dimension for vector in embeddings):
            raise VectorStoreError("Embeddings must be non-empty and equally sized")

        rows = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            rows.append(
                (
                    chunk.chunk_id,
                    chunk.document_id,
                    chunk.document_name,
                    chunk.chunk_index,
                    chunk.text,
                    chunk.token_count,
                    chunk.chunking_strategy,
                    json.dumps(chunk.page_numbers),
                    json.dumps(chunk.section_titles),
                    json.dumps(list(embedding)),
                    dimension,
                )
            )
        self._connection.executemany(
            """
            INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                document_id=excluded.document_id,
                document_name=excluded.document_name,
                chunk_index=excluded.chunk_index,
                text=excluded.text,
                token_count=excluded.token_count,
                chunking_strategy=excluded.chunking_strategy,
                page_numbers=excluded.page_numbers,
                section_titles=excluded.section_titles,
                embedding=excluded.embedding,
                embedding_dimension=excluded.embedding_dimension
            """,
            rows,
        )
        self._connection.commit()

    def search(
        self,
        query_embedding: Sequence[float],
        top_k: int,
        metadata_filter: Mapping[str, object] | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        if top_k < 1:
            raise ValueError("top_k must be at least one")
        if not query_embedding:
            raise VectorStoreError("Query embedding cannot be empty")

        clauses, parameters = self._filter_query(metadata_filter or {})
        statement = "SELECT * FROM chunks"
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        rows = self._connection.execute(statement, parameters).fetchall()

        results: list[RetrievedChunk] = []
        for row in rows:
            vector = tuple(json.loads(row["embedding"]))
            if len(vector) != len(query_embedding):
                raise VectorStoreError("Query embedding dimension does not match index")
            chunk = DocumentChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                document_name=row["document_name"],
                chunk_index=row["chunk_index"],
                text=row["text"],
                token_count=row["token_count"],
                chunking_strategy=row["chunking_strategy"],
                page_numbers=tuple(json.loads(row["page_numbers"])),
                section_titles=tuple(json.loads(row["section_titles"])),
            )
            results.append(RetrievedChunk(chunk=chunk, score=_cosine(query_embedding, vector)))
        return tuple(sorted(results, key=lambda item: item.score, reverse=True)[:top_k])

    @staticmethod
    def _filter_query(metadata_filter: Mapping[str, object]) -> tuple[list[str], list[object]]:
        supported = {"document_id", "document_name", "chunking_strategy"}
        unknown = set(metadata_filter) - supported
        if unknown:
            raise ValueError(f"Unsupported metadata filter(s): {sorted(unknown)}")
        return [f"{key} = ?" for key in metadata_filter], list(metadata_filter.values())


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise VectorStoreError("Embeddings cannot have zero magnitude")
    return numerator / (left_norm * right_norm)
