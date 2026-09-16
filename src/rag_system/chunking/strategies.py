"""Chunking strategies used for controlled retrieval experiments."""

from __future__ import annotations

from dataclasses import dataclass

from rag_system.schemas import DocumentChunk, DocumentSegment, ParsedDocument


class InvalidChunkingConfiguration(ValueError):
    """Raised when chunk-size or overlap settings are invalid."""


@dataclass(frozen=True, slots=True)
class _TokenWithProvenance:
    value: str
    page_number: int | None
    section_title: str | None


def _validate(chunk_size: int, overlap: int) -> None:
    if chunk_size < 1:
        raise InvalidChunkingConfiguration("chunk_size must be at least one")
    if overlap < 0 or overlap >= chunk_size:
        raise InvalidChunkingConfiguration(
            "overlap must be zero or greater and smaller than chunk_size"
        )


def _tokens(segment: DocumentSegment) -> list[_TokenWithProvenance]:
    return [
        _TokenWithProvenance(
            value=token,
            page_number=segment.page_number,
            section_title=segment.section_title,
        )
        for token in segment.text.split()
    ]


def _unique_values[T](values: list[T | None]) -> tuple[T, ...]:
    result: list[T] = []
    for value in values:
        if value is not None and value not in result:
            result.append(value)
    return tuple(result)


def _build_chunk(
    document: ParsedDocument,
    chunk_index: int,
    strategy: str,
    tokens: list[_TokenWithProvenance],
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{document.document_id}_c{chunk_index:04d}",
        document_id=document.document_id,
        document_name=document.document_name,
        chunk_index=chunk_index,
        text=" ".join(token.value for token in tokens),
        token_count=len(tokens),
        chunking_strategy=strategy,
        page_numbers=_unique_values([token.page_number for token in tokens]),
        section_titles=_unique_values([token.section_title for token in tokens]),
    )


class FixedTokenChunker:
    """Create sliding fixed-size chunks across the entire normalized document."""

    strategy_name = "fixed_token"

    def __init__(self, chunk_size: int, overlap: int = 0) -> None:
        _validate(chunk_size, overlap)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document: ParsedDocument) -> tuple[DocumentChunk, ...]:
        tokens = [token for segment in document.segments for token in _tokens(segment)]
        return self._chunk_tokens(document, tokens)

    def _chunk_tokens(
        self,
        document: ParsedDocument,
        tokens: list[_TokenWithProvenance],
    ) -> tuple[DocumentChunk, ...]:
        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.overlap
        for start in range(0, len(tokens), step):
            window = tokens[start : start + self.chunk_size]
            if not window:
                break
            chunks.append(
                _build_chunk(document, len(chunks), self.strategy_name, window)
            )
            if start + self.chunk_size >= len(tokens):
                break
        return tuple(chunks)


class SectionAwareChunker(FixedTokenChunker):
    """Chunk each source page or Markdown section without crossing its boundary."""

    strategy_name = "section_aware"

    def chunk(self, document: ParsedDocument) -> tuple[DocumentChunk, ...]:
        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.overlap

        for segment in document.segments:
            tokens = _tokens(segment)
            for start in range(0, len(tokens), step):
                window = tokens[start : start + self.chunk_size]
                if not window:
                    break
                chunks.append(
                    _build_chunk(document, len(chunks), self.strategy_name, window)
                )
                if start + self.chunk_size >= len(tokens):
                    break
        return tuple(chunks)
