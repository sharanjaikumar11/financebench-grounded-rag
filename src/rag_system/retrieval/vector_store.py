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
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS vector_store_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self._connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_after_insert AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
            END
            """
        )
        self._connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_after_delete AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
            END
            """
        )
        self._connection.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_after_update AFTER UPDATE OF text ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
                INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
            END
            """
        )
        schema_version = self._connection.execute(
            "SELECT value FROM vector_store_metadata WHERE key = 'fts_schema_version'"
        ).fetchone()
        if schema_version is None:
            self._connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
            self._connection.execute(
                "INSERT INTO vector_store_metadata(key, value) VALUES ('fts_schema_version', '1')"
            )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def infer_filing_metadata_filter(self, question: str) -> Mapping[str, object]:
        """Infer one exact filing from a company name and year present in the index.

        This is intentionally conservative: it returns a filter only when the
        normalized company name and one year identify exactly one indexed filing.
        """
        normalized_question = self._normalize_name(question)
        quarter_match = re.search(
            r"\b(?:Q([1-4])\s*(?:FY)?(20\d{2})|(?:FY)?(20\d{2})\s*Q([1-4]))\b",
            question,
            flags=re.IGNORECASE,
        )
        if quarter_match:
            quarter = quarter_match.group(1) or quarter_match.group(4)
            year = quarter_match.group(2) or quarter_match.group(3)
            quarterly_names = self._connection.execute(
                "SELECT DISTINCT document_name FROM chunks WHERE document_name LIKE ?",
                (f"%_{year}Q{quarter}_%",),
            ).fetchall()
            quarterly_matches = [
                row["document_name"]
                for row in quarterly_names
                if self._normalized_company_name(row["document_name"], year) in normalized_question
            ]
            if len(quarterly_matches) == 1:
                return {"document_name": quarterly_matches[0]}
        dated_match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d{2})\b",
            question,
            flags=re.IGNORECASE,
        )
        if dated_match:
            month_numbers = {
                "january": "01", "february": "02", "march": "03", "april": "04",
                "may": "05", "june": "06", "july": "07", "august": "08",
                "september": "09", "october": "10", "november": "11", "december": "12",
            }
            date_suffix = (
                f"dated-{dated_match.group(3)}-"
                f"{month_numbers[dated_match.group(1).casefold()]}-"
                f"{int(dated_match.group(2)):02d}.pdf"
            )
            dated_names = self._connection.execute(
                "SELECT DISTINCT document_name FROM chunks WHERE document_name LIKE ?",
                (f"%{date_suffix}",),
            ).fetchall()
            dated_matches = [
                row["document_name"]
                for row in dated_names
                if self._normalized_company_name(row["document_name"]) in normalized_question
            ]
            if len(dated_matches) == 1:
                return {"document_name": dated_matches[0]}

        years = sorted(
            set(re.findall(r"\b(?:FY)?(20\d{2})\b", question, flags=re.IGNORECASE)),
            reverse=True,
        )
        if not years:
            return {}

        # A comparison such as "FY2018-to-FY2019" is normally answered from
        # the later annual filing, which contains both comparative periods.
        # Select that filing only when the index makes the company/year choice
        # unambiguous; this avoids guessing a document outside the corpus.
        year = years[0]
        names = self._connection.execute(
            "SELECT DISTINCT document_name FROM chunks WHERE document_name LIKE ?",
            (f"%_{year}%",),
        ).fetchall()
        matches = [
            row["document_name"]
            for row in names
            if (normalized_company := self._normalized_company_name(row["document_name"], year))
            and normalized_company in normalized_question
        ]
        if len(matches) == 1:
            return {"document_name": matches[0]}

        # FinanceBench annual questions can have a same-year 10-Q as well as
        # a 10-K in the index.  Unless the question explicitly names a quarter,
        # prefer the annual filing rather than failing the retrieval entirely.
        annual_matches = [name for name in matches if "_10K" in name.upper()]
        if len(annual_matches) == 1:
            return {"document_name": annual_matches[0]}
        return {}

    @staticmethod
    def _normalized_company_name(document_name: str, year: str | None = None) -> str:
        """Return the normalized company part of a FinanceBench-style file name."""
        company_name = re.split(rf"_{year}(?:Q\d+)?_", document_name, maxsplit=1)[0] if year else re.split(
            r"_20\d{2}(?:Q\d+)?_", document_name, maxsplit=1
        )[0]
        return SQLiteVectorStore._normalize_name(company_name)

    @staticmethod
    def _normalize_name(value: str) -> str:
        """Normalize company names while treating '&' and 'and' equivalently."""
        return re.sub(r"[^A-Za-z0-9]", "", re.sub(r"\band\b", "", value, flags=re.IGNORECASE)).upper()

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
        candidate_document_ids: Sequence[str] | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        if top_k < 1:
            raise ValueError("top_k must be at least one")
        if not query_embedding:
            raise VectorStoreError("Query embedding cannot be empty")

        clauses, parameters = self._filter_query(metadata_filter or {})
        if candidate_document_ids is not None:
            if not candidate_document_ids:
                return ()
            placeholders = ", ".join("?" for _ in candidate_document_ids)
            clauses.append(f"document_id IN ({placeholders})")
            parameters.extend(candidate_document_ids)
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
        # Financial statement rows can be ranked below narrative mentions by
        # either dense or lexical retrieval.  Keep a wider local candidate set
        # so the table-aware lexical rerank can promote the direct row.
        clauses, parameters = self._filter_query(metadata_filter or {})
        candidate_count = max(top_k * 25, 200)
        # Once a query is safely scoped to one filing, every matching chunk in
        # that filing is a practical candidate.  This prevents a table row
        # from being discarded behind repeated narrative references to the
        # same term while keeping unfiltered corpus-wide retrieval bounded.
        if metadata_filter and "document_name" in metadata_filter:
            count_statement = "SELECT COUNT(*) AS chunk_count FROM chunks"
            if clauses:
                count_statement += " WHERE " + " AND ".join(clauses)
            candidate_count = max(
                candidate_count,
                self._connection.execute(count_statement, parameters).fetchone()["chunk_count"],
            )
        terms = _sparse_query_terms(query)
        if not terms:
            return self.search(query_embedding, top_k, metadata_filter)
        statement = "SELECT chunks.* FROM chunks_fts JOIN chunks ON chunks_fts.rowid = chunks.rowid WHERE chunks_fts MATCH ?"
        if clauses:
            statement += " AND " + " AND ".join(f"chunks.{clause}" for clause in clauses)
        statement += " ORDER BY bm25(chunks_fts) LIMIT ?"
        sparse_rows = self._connection.execute(statement, [terms, *parameters, candidate_count]).fetchall()
        sparse = [RetrievedChunk(self._row_to_chunk(row), 0.0) for row in sparse_rows]
        sparse = sorted(
            sparse,
            key=lambda item: _financial_keyword_relevance(item.chunk.text, query),
            reverse=True,
        )
        candidate_document_ids = tuple(dict.fromkeys(item.chunk.document_id for item in sparse))
        dense = self.search(
            query_embedding,
            candidate_count,
            metadata_filter,
            candidate_document_ids=candidate_document_ids or None,
        )
        fused: dict[str, tuple[DocumentChunk, float]] = {}
        for rank, item in enumerate(dense, start=1):
            fused[item.chunk.chunk_id] = (item.chunk, 1 / (60 + rank))
        for rank, item in enumerate(sparse, start=1):
            chunk, score = fused.get(item.chunk.chunk_id, (item.chunk, 0.0))
            fused[item.chunk.chunk_id] = (chunk, score + 1 / (60 + rank))
        # Avoid spending all top-k slots on consecutive chunks from the same
        # table or paragraph.  Adjacent text is added later for context, so
        # diversified anchors give the generator broader evidence coverage.
        selected: list[RetrievedChunk] = []
        for chunk, score in sorted(
            fused.values(),
            key=lambda value: value[1] + _financial_keyword_relevance(value[0].text, query),
            reverse=True,
        ):
            is_near_selected = any(
                candidate.chunk.document_id == chunk.document_id
                and abs(candidate.chunk.chunk_index - chunk.chunk_index) <= 2
                for candidate in selected
            )
            if is_near_selected:
                continue
            selected.append(RetrievedChunk(chunk, score))
            if len(selected) == top_k:
                break
        return tuple(selected)

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
        return tuple(sorted(expanded, key=lambda item: item.score, reverse=True))

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
    """Build an OR query from the meaningful terms in any user question."""
    stop_words = {
        "answer", "amount", "based", "details", "from", "give", "shown", "that",
        "the", "this", "using", "what", "with", "would", "year",
    }
    terms = {
        term.casefold()
        for term in re.findall(r"[A-Za-z0-9]+", query)
        if len(term) > 2 and term.casefold() not in stop_words
    }
    return " OR ".join(sorted(terms))


def _financial_keyword_relevance(text: str, query: str) -> float:
    """Rerank FTS candidates by coverage of meaningful financial terms."""
    stop_words = {
        "answer", "amount", "based", "briefly", "does", "explain", "from", "give",
        "have", "healthy", "its", "million", "millions", "of", "on", "percent",
        "question", "round", "shown", "state", "that", "the", "this", "to", "usd", "using",
        "was", "were", "what", "with", "would", "year",
    }
    query_terms = [
        term.casefold()
        for term in re.findall(r"[A-Za-z0-9]+", query)
        if len(term) > 2 and term.casefold() not in stop_words and not term.casefold().startswith("fy")
    ]
    if not query_terms:
        return 0.0
    normalized_text = text.casefold()
    text_terms = {
        _financial_term_stem(term)
        for term in re.findall(r"[A-Za-z0-9]+", normalized_text)
    }
    matched = sum(_financial_term_stem(term) in text_terms for term in set(query_terms))
    # Rows in statements normally contain several figures, while narrative
    # text and a table of contents do not.  This makes the preference generic
    # to financial tables rather than tied to any company or benchmark case.
    numeric_density = min(len(re.findall(r"\b\d[\d,().%$-]*\b", text)), 8) / 40
    statement_heading = bool(
        re.search(
            r"\b(?:consolidated\s+)?(?:balance\s+sheets?|income\s+statements?|"
            r"statements?\s+of\s+(?:income|operations|cash\s+flows)|cash\s+flows?)\b",
            normalized_text,
        )
    )
    return matched / len(set(query_terms)) + numeric_density + (0.5 if statement_heading else 0.0)


def _financial_term_stem(term: str) -> str:
    """Normalize common singular/plural variations in statement labels."""
    if term.endswith("ies") and len(term) > 4:
        return term[:-3] + "y"
    if term.endswith("s") and not term.endswith("ss") and len(term) > 3:
        return term[:-1]
    return term
