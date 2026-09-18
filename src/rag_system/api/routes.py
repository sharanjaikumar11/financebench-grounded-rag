"""HTTP routes for document indexing and grounded RAG queries."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from rag_system.services.query import RAGQueryService


class IndexRequest(BaseModel):
    source_path: Path


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    metadata_filter: dict[str, str] | None = None


def create_router(service: RAGQueryService) -> APIRouter:
    """Create routes bound to a configured RAG service."""
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/index")
    def index_document(request: IndexRequest) -> dict[str, object]:
        try:
            result = service.index_document(request.source_path)
        except FileNotFoundError as error:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
        except (ValueError, RuntimeError) as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
        return {"status": result.status, "document_id": result.document_id, "chunk_count": result.chunk_count}

    @router.post("/query")
    def query(request: QueryRequest) -> dict[str, object]:
        try:
            response = service.answer(request.question, request.metadata_filter)
        except (ValueError, RuntimeError) as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
        return {
            "answer": response.answer.text,
            "insufficient_context": response.answer.insufficient_context,
            "citations": [
                {"source_label": citation.source_label, "document_id": citation.document_id,
                 "document_name": citation.document_name, "page_numbers": citation.page_numbers,
                 "section_titles": citation.section_titles}
                for citation in response.answer.citations
            ],
        }

    return router
