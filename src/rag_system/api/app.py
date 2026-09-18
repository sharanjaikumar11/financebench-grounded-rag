"""FastAPI application factory."""

from fastapi import FastAPI

from rag_system.api.routes import create_router
from rag_system.services.query import RAGQueryService


def create_app(service: RAGQueryService) -> FastAPI:
    """Create the HTTP application without hidden global dependencies."""
    app = FastAPI(title="Production RAG System")
    app.include_router(create_router(service))
    return app
