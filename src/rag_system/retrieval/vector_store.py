"""SQLite-backed persistent vector store for dense chunk retrieval."""

from __future__ import annotations

import json
import math
import re
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
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
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
        self._connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, content='chunks', content_rowid='rowid')"
        )
        self._connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
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

    def hybrid_search(
        self, query_embedding: Sequence[float], query: str, top_k: int,
        metadata_filter: Mapping[str, object] | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        """Fuse dense and exact-term ranking with reciprocal-rank fusion."""
        candidate_count = max(top_k * 10, 50)
        dense = self.search(query_embedding, candidate_count, metadata_filter)
        clauses, parameters = self._filter_query(metadata_filter or {})
        terms = _sparse_query_terms(query)
        if not terms:
            return dense[:top_k]
        statement = "SELECT chunks.* FROM chunks_fts JOIN chunks ON chunks_fts.rowid = chunks.rowid WHERE chunks_fts MATCH ?"
        if clauses:
            statement += " AND " + " AND ".join(f"chunks.{clause}" for clause in clauses)
        statement += " ORDER BY bm25(chunks_fts) LIMIT ?"
        sparse_rows = self._connection.execute(statement, [terms, *parameters, candidate_count]).fetchall()
        sparse = [RetrievedChunk(self._row_to_chunk(row), 0.0) for row in sparse_rows]
        fused: dict[str, tuple[DocumentChunk, float]] = {}
        for rank, item in enumerate(dense, start=1):
            fused[item.chunk.chunk_id] = (item.chunk, 1 / (60 + rank))
        for rank, item in enumerate(sparse, start=1):
            chunk, score = fused.get(item.chunk.chunk_id, (item.chunk, 0.0))
            fused[item.chunk.chunk_id] = (chunk, score + 1 / (60 + rank))
        return tuple(
            RetrievedChunk(chunk, score)
            for chunk, score in sorted(fused.values(), key=lambda value: value[1], reverse=True)[:top_k]
        )

    def expand_with_neighbors(
        self, results: Sequence[RetrievedChunk], radius: int = 1
    ) -> tuple[RetrievedChunk, ...]:
        """Preserve table and sentence context across fixed-token chunk boundaries."""
        if radius < 0:
            raise ValueError("radius cannot be negative")
        expanded: list[RetrievedChunk] = []
        seen: set[str] = set()
        for result in results:
            rows = self._connection.execute(
                """
                SELECT * FROM chunks
                WHERE document_id = ? AND chunking_strategy = ?
                  AND chunk_index BETWEEN ? AND ?
                ORDER BY chunk_index
                """,
                (
                    result.chunk.document_id,
                    result.chunk.chunking_strategy,
                    result.chunk.chunk_index - radius,
                    result.chunk.chunk_index + radius,
                ),
            ).fetchall()
            for row in rows:
                chunk = self._row_to_chunk(row)
                if chunk.chunk_id in seen:
                    continue
                seen.add(chunk.chunk_id)
                score = result.score if chunk.chunk_id == result.chunk.chunk_id else result.score - 0.0001
                expanded.append(RetrievedChunk(chunk, score))
        return tuple(expanded)

    @staticmethod
    def _row_to_chunk(row: sqlite3.Row) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=row["chunk_id"], document_id=row["document_id"],
            document_name=row["document_name"], chunk_index=row["chunk_index"],
            text=row["text"], token_count=row["token_count"],
            chunking_strategy=row["chunking_strategy"],
            page_numbers=tuple(json.loads(row["page_numbers"])),
            section_titles=tuple(json.loads(row["section_titles"])),
        )

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


def _sparse_query_terms(query: str) -> str:
    """Build an OR query from meaningful finance terms and common filing aliases."""
    stop_words = {
        "answer", "amount", "based", "details", "from", "give", "shown", "that",
        "the", "this", "using", "what", "with", "would", "year",
    }
    terms = {
        term.casefold()
        for term in re.findall(r"[A-Za-z0-9]+", query)
        if len(term) > 2 and term.casefold() not in stop_words
    }
    normalized_query = query.casefold()
    if "capital expenditure" in normalized_query or "capex" in normalized_query:
        terms.update({"purchases", "property", "plant", "equipment", "investing", "activities"})
    if "ppne" in normalized_query:
        terms.update({"property", "plant", "equipment", "net", "assets", "balance"})
    if "capital-intensive" in normalized_query or "capital intensive" in normalized_query:
        terms.update({"capital", "spending", "property", "plant", "equipment", "sales"})
    return " OR ".join(sorted(terms))
