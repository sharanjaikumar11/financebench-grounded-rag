"""Experimental page-local table rows alongside ordinary narrative chunks."""

from dataclasses import replace

import pymupdf

from rag_system.chunking.strategies import SectionAwareChunker
from rag_system.schemas import DocumentChunk, ParsedDocument, SourceFormat


def serialize_table_rows(
    rows: list[list[str | None]], headers: list[str | None]
) -> tuple[str, ...]:
    """Keep physical columns, including empty cells; never infer missing periods."""
    result = []
    names = [" ".join((name or "").split()) for name in headers]
    for row in rows:
        values = [" ".join((value or "").split()) for value in row]
        if not any(values):
            continue
        cells = [
            f"Column {i + 1} ({names[i] if i < len(names) and names[i] else 'unlabelled'}): {value or '[empty]'}"
            for i, value in enumerate(values)
        ]
        result.append(" | ".join(cells))
    return tuple(result)


class TableAwareChunker(SectionAwareChunker):
    """Retain narrative plus one unsplit record per detected table row.

    Uses geometric ruled-table detection. Borderless, merged and scanned tables
    can remain narrative-only; no invented column labels or OCR is applied.
    Build in a separate storage directory to compare against the baseline.
    """

    strategy_name = "table_aware_v1"

    def chunk(self, document: ParsedDocument) -> tuple[DocumentChunk, ...]:
        chunks = [
            replace(chunk, chunk_id=f"{document.document_id}_table_v1_c{chunk.chunk_index:04d}")
            for chunk in super().chunk(document)
        ]
        if document.source_format != SourceFormat.PDF:
            return tuple(chunks)
        with pymupdf.open(document.source_path) as pdf:
            for page_index, page in enumerate(pdf):
                for table_index, table in enumerate(page.find_tables().tables):
                    # Preserve nearby source text as context, without guessing which
                    # line is a title/unit or propagating units across unrelated tables.
                    x0, y0, x1, _ = table.bbox
                    context = page.get_text("text", clip=pymupdf.Rect(x0, max(0, y0 - 70), x1, y0))
                    context = " ".join(context.split())
                    rows = table.extract()
                    headers = table.header.names
                    # Detectors sometimes call the first data row a header. Retain
                    # it, and explicitly qualify the labels instead of losing facts.
                    for row_index, row in enumerate(serialize_table_rows(rows, headers)):
                        text = (
                            f"PDF page {page_index + 1}; Table {table_index + 1}; Nearby text: {context}\n"
                            "Parenthesized column labels are automatically detected header candidates; "
                            "verify periods and units against the source context.\n"
                            f"{row}"
                        )
                        index = len(chunks)
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{document.document_id}_table_v1_c{index:04d}",
                                document_id=document.document_id,
                                document_name=document.document_name,
                                chunk_index=index,
                                text=text,
                                token_count=len(text.split()),
                                chunking_strategy=self.strategy_name,
                                page_numbers=(page_index + 1,),
                                section_titles=(f"Table {table_index + 1}, row {row_index + 1}",),
                            )
                        )
        return tuple(chunks)
