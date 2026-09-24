"""Lead-demo interface for the grounded FinanceBench RAG system."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

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


def citation_label(citation: object) -> str:
    return (
        f"{citation.document_name} | pages "
        f"{', '.join(str(page) for page in citation.page_numbers) or 'not available'}"
    )


def citation_url(citation: object) -> str | None:
    """Build a page-specific local PDF link for an indexed FinanceBench source."""
    document_name = Path(citation.document_name).name
    source_path = (SOURCE_DIRECTORY / document_name).resolve()
    if source_path.parent != SOURCE_DIRECTORY or not source_path.is_file():
        return None
    page_number = citation.page_numbers[0] if citation.page_numbers else 1
    return f"{source_path.as_uri()}#page={page_number}"


def render_citation(citation: object, key: str) -> None:
    """Show a source link when the cited PDF remains available locally."""
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
