"""Lead-demo interface for the grounded FinanceBench RAG system."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import perf_counter
from urllib.parse import quote, unquote

import streamlit as st

from rag_system.chunking import FixedTokenChunker
from rag_system.config import Settings
from rag_system.generation.answering import (
    GeminiAnswerProvider,
    GroqAnswerProvider,
    GroundedAnswerGenerator,
)
from rag_system.ingestion.pipeline import DocumentIngestor, DocumentRegistry
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.services.query import RAGQueryService

INDEX_DIRECTORY = "data/processed/local_sentence_transformers"
SOURCE_DIRECTORY = Path("data/raw/financebench/pdfs").resolve()
PDF_SERVER_HOST = "127.0.0.1"
PDF_SERVER_PORT = int(os.getenv("FINANCEBENCH_PDF_SERVER_PORT", "8502"))
SUGGESTIONS = {
    "FY2018 net PP&E": (
        "Assume that you are a public equities analyst. Answer the following question "
        "by primarily using information that is shown in the balance sheet: what is the "
        "year end FY2018 net PPNE for 3M? Answer in USD billions."
    ),
    "Safe abstention": "What is the CEO's favourite colour?",
}


@st.cache_resource
def retriever() -> HybridRetriever:
    """Create one shared local retrieval stack for the Streamlit process."""
    from pathlib import Path

    storage = Path(INDEX_DIRECTORY)
    return HybridRetriever(
        SentenceTransformerEmbeddingProvider(),
        SQLiteVectorStore(storage / "vectors.sqlite3"),
    )


@st.cache_resource
def query_service() -> RAGQueryService:
    """Create one shared grounded-answer service for the Streamlit process."""
    settings = Settings.from_environment()
    if settings.answer_provider == "groq":
        provider = GroqAnswerProvider(settings.require_groq_key(), settings.groq_model)
    else:
        provider = GeminiAnswerProvider(
            settings.require_gemini_key(),
            settings.gemini_model,
            settings.gemini_fallback_model,
            settings.gemini_thinking_level,
        )
    from pathlib import Path

    storage = Path(INDEX_DIRECTORY)
    return RAGQueryService(
        ingestor=DocumentIngestor(DocumentRegistry(storage / "documents.sqlite3")),
        chunker=FixedTokenChunker(200, 40),
        retriever=retriever(),
        answer_generator=GroundedAnswerGenerator(
            provider
        ),
        top_k=3,
    )


class _LocalPdfRequestHandler(BaseHTTPRequestHandler):
    """Serve only PDFs in the selected FinanceBench source directory."""

    server_version = "FinanceBenchPdfServer/1.0"

    def do_GET(self) -> None:  # noqa: N802 - required HTTP handler name
        self._serve_pdf(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802 - required HTTP handler name
        self._serve_pdf(include_body=False)

    def _serve_pdf(self, include_body: bool) -> None:
        document_name = Path(unquote(self.path.split("?", 1)[0])).name
        pdf_path = (SOURCE_DIRECTORY / document_name).resolve()
        if (
            pdf_path.parent != SOURCE_DIRECTORY
            or pdf_path.suffix.lower() != ".pdf"
            or not pdf_path.is_file()
        ):
            self.send_error(404, "PDF not found")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(pdf_path.stat().st_size))
        self.send_header("Content-Disposition", f'inline; filename="{pdf_path.name}"')
        self.end_headers()
        if include_body:
            with pdf_path.open("rb") as pdf_file:
                shutil.copyfileobj(pdf_file, self.wfile)

    def log_message(self, format: str, *args: object) -> None:
        """Keep local PDF requests out of the Streamlit terminal output."""


@dataclass(frozen=True)
class _LocalPdfServer:
    port: int

    @property
    def base_url(self) -> str:
        return f"http://{PDF_SERVER_HOST}:{self.port}"


@st.cache_resource
def pdf_source_server() -> _LocalPdfServer:
    """Start a loopback-only PDF server, separate from Streamlit static serving."""
    try:
        server = ThreadingHTTPServer((PDF_SERVER_HOST, PDF_SERVER_PORT), _LocalPdfRequestHandler)
    except OSError as error:
        raise RuntimeError(
            f"Could not start the local PDF source server on port {PDF_SERVER_PORT}. "
            "Set FINANCEBENCH_PDF_SERVER_PORT to an available port and restart Streamlit."
        ) from error
    Thread(target=server.serve_forever, name="financebench-pdf-server", daemon=True).start()
    return _LocalPdfServer(PDF_SERVER_PORT)


def citation_label(citation: object) -> str:
    return (
        f"{citation.document_name} | pages "
        f"{', '.join(str(page) for page in citation.page_numbers) or 'not available'}"
    )


def citation_url(citation: object) -> str | None:
    """Build an HTTP-served PDF link that opens at the cited page."""
    document_name = Path(citation.document_name).name
    source_path = (SOURCE_DIRECTORY / document_name).resolve()
    if source_path.parent != SOURCE_DIRECTORY or not source_path.is_file():
        return None
    page_number = citation.page_numbers[0] if citation.page_numbers else 1
    return f"{pdf_source_server().base_url}/{quote(document_name)}#page={page_number}"


def render_citation(citation: object, key: str) -> None:
    """Show a page-specific source link to the local loopback PDF server."""
    if not hasattr(citation, "document_name"):
        st.caption(f":material/description: {citation}")
        return
    label = citation_label(citation)
    url = citation_url(citation)
    if url:
        st.link_button(
            label,
            url,
            key=key,
            type="tertiary",
            icon=":material/open_in_new:",
        )
    else:
        st.caption(f":material/description: {label}")


def render_answer(text: str) -> None:
    """Display monetary values literally instead of as Markdown math."""
    st.markdown(text.replace("$", r"\$"))


st.set_page_config(page_title="FinanceBench RAG demo", page_icon=":material/analytics:", layout="wide")
st.title("FinanceBench grounded RAG")
st.caption("Local embeddings and hybrid retrieval with source-cited answers.")

with st.sidebar:
    st.subheader("Demo configuration")
    st.write("**Index:** Fixed-token, 200 tokens, 40 overlap")
    st.write("**Retrieval:** SentenceTransformer + SQLite FTS5/BM25 hybrid")
    st.write(f"**Generation:** {Settings.from_environment().answer_provider.title()}, temperature 0")
    st.divider()
    st.caption("Answers include only sources retrieved from the selected FinanceBench filing.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    choice = st.pills("Try a validated demo question", list(SUGGESTIONS), selection_mode="single")
    if choice:
        st.session_state.pending_question = SUGGESTIONS[choice]
        st.rerun()

for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        render_answer(message["content"])
        for index, citation in enumerate(message.get("citations", ())):
            render_citation(citation, f"history-{message.get('id', message_index)}-{index}")

question = st.session_state.pop("pending_question", None) or st.chat_input(
    "Ask a question about the indexed filings", submit_mode="disable"
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        render_answer(question)

    with st.chat_message("assistant"):
        try:
            with st.status(":shimmer[Retrieving source evidence]", type="compact") as status:
                started_at = perf_counter()
                response = query_service().answer(question)
                elapsed_seconds = perf_counter() - started_at
                status.update(label=f"Answer ready in {elapsed_seconds:.1f} seconds", state="complete")
        except ValueError as error:
            st.error(str(error))
        except RuntimeError as error:
            st.error(f"Query failed: {error}")
        else:
            if response.answer.insufficient_context:
                st.warning("INSUFFICIENT_CONTEXT — the retrieved sources do not support a reliable answer.")
                content = "INSUFFICIENT_CONTEXT"
                citations: tuple[str, ...] = ()
            else:
                render_answer(response.answer.text)
                citations = response.answer.citations
                with st.container(border=True):
                    st.subheader("Sources")
                    for index, citation in enumerate(citations):
                        render_citation(citation, f"current-{index}")
                st.caption(f"Response time: {elapsed_seconds:.1f} seconds")
                content = response.answer.text
            st.session_state.messages.append(
                {
                    "id": len(st.session_state.messages),
                    "role": "assistant",
                    "content": content,
                    "citations": citations,
                }
            )
