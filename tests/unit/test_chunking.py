from pathlib import Path

import pytest

from rag_system.chunking.strategies import (
    FixedTokenChunker,
    InvalidChunkingConfiguration,
    SectionAwareChunker,
)
from rag_system.schemas import DocumentSegment, ParsedDocument, SourceFormat


def make_document(*segments: DocumentSegment) -> ParsedDocument:
    return ParsedDocument(
        document_id="doc_test",
        document_name="test.md",
        source_path=Path("test.md"),
        source_format=SourceFormat.MARKDOWN,
        content_hash="content-hash",
        segments=segments,
    )


def test_fixed_token_chunker_uses_overlap_and_stable_ids() -> None:
    document = make_document(
        DocumentSegment(0, "one two three four five six", page_number=1)
    )

    chunks = FixedTokenChunker(chunk_size=3, overlap=1).chunk(document)

    assert [chunk.text for chunk in chunks] == [
        "one two three",
        "three four five",
        "five six",
    ]
    assert [chunk.chunk_id for chunk in chunks] == [
        "doc_test_c0000",
        "doc_test_c0001",
        "doc_test_c0002",
    ]
    assert all(chunk.chunking_strategy == "fixed_token" for chunk in chunks)


def test_fixed_token_chunker_retains_page_provenance_across_boundaries() -> None:
    document = make_document(
        DocumentSegment(0, "one two", page_number=1),
        DocumentSegment(1, "three four", page_number=2),
    )

    chunks = FixedTokenChunker(chunk_size=3).chunk(document)

    assert chunks[0].page_numbers == (1, 2)
    assert chunks[1].page_numbers == (2,)


def test_section_aware_chunker_never_mixes_markdown_sections() -> None:
    document = make_document(
        DocumentSegment(0, "revenue improved strongly", section_title="Overview"),
        DocumentSegment(1, "demand could decline", section_title="Risks"),
    )

    chunks = SectionAwareChunker(chunk_size=4).chunk(document)

    assert [chunk.text for chunk in chunks] == [
        "revenue improved strongly",
        "demand could decline",
    ]
    assert [chunk.section_titles for chunk in chunks] == [("Overview",), ("Risks",)]
    assert all(chunk.chunking_strategy == "section_aware" for chunk in chunks)


def test_section_aware_chunker_splits_a_long_source_section() -> None:
    document = make_document(
        DocumentSegment(0, "one two three four five", section_title="Overview")
    )

    chunks = SectionAwareChunker(chunk_size=3, overlap=1).chunk(document)

    assert [chunk.text for chunk in chunks] == [
        "one two three",
        "three four five",
    ]
    assert all(chunk.section_titles == ("Overview",) for chunk in chunks)


@pytest.mark.parametrize("chunk_size, overlap", [(0, 0), (2, -1), (2, 2)])
def test_chunkers_reject_invalid_configuration(chunk_size: int, overlap: int) -> None:
    with pytest.raises(InvalidChunkingConfiguration):
        FixedTokenChunker(chunk_size=chunk_size, overlap=overlap)
