from pathlib import Path

import pymupdf
import pytest

from rag_system.ingestion.parsers import EmptyDocumentError, UnsupportedDocumentError
from rag_system.ingestion.pipeline import DocumentIngestor, DocumentRegistry


def make_ingestor(tmp_path: Path) -> DocumentIngestor:
    return DocumentIngestor(DocumentRegistry(tmp_path / "manifest.sqlite3"))


def test_ingests_normalized_text_with_stable_metadata(tmp_path: Path) -> None:
    source = tmp_path / "policy.txt"
    source.write_text("  Revenue\r\n\r\n  increased\tby 10%.  ", encoding="utf-8")

    result = make_ingestor(tmp_path).ingest(source)

    assert result.status == "ingested"
    assert result.document is not None
    assert result.document.document_name == "policy.txt"
    assert result.document.document_id.startswith("doc_")
    assert result.document.segments[0].text == "Revenue\n\nincreased by 10%."
    assert result.document.segments[0].page_number is None


def test_marks_identical_content_as_duplicate(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("same content", encoding="utf-8")
    second.write_text("same content", encoding="utf-8")
    ingestor = make_ingestor(tmp_path)

    assert ingestor.ingest(first).status == "ingested"
    assert ingestor.ingest(second).status == "duplicate"


def test_preserves_markdown_section_metadata(tmp_path: Path) -> None:
    source = tmp_path / "report.md"
    source.write_text(
        "# Overview\nRevenue improved.\n\n## Risks\nDemand may decline.",
        encoding="utf-8",
    )

    document = make_ingestor(tmp_path).ingest(source).document

    assert document is not None
    assert [segment.section_title for segment in document.segments] == ["Overview", "Risks"]
    assert [segment.text for segment in document.segments] == [
        "Revenue improved.",
        "Demand may decline.",
    ]


def test_preserves_pdf_page_metadata(tmp_path: Path) -> None:
    source = tmp_path / "report.pdf"
    pdf = pymupdf.open()
    page_one = pdf.new_page()
    page_one.insert_text((72, 72), "First page evidence")
    page_two = pdf.new_page()
    page_two.insert_text((72, 72), "Second page evidence")
    pdf.save(source)
    pdf.close()

    document = make_ingestor(tmp_path).ingest(source).document

    assert document is not None
    assert [segment.page_number for segment in document.segments] == [1, 2]
    assert "First page evidence" in document.segments[0].text
    assert "Second page evidence" in document.segments[1].text


def test_rejects_empty_documents(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text(" \n\t ", encoding="utf-8")

    with pytest.raises(EmptyDocumentError):
        make_ingestor(tmp_path).ingest(source)


def test_rejects_unsupported_formats(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    source.write_bytes(b"not a supported source")

    with pytest.raises(UnsupportedDocumentError):
        make_ingestor(tmp_path).ingest(source)
