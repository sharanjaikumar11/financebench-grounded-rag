import pytest

from rag_system.generation.answering import GeminiAnswerProvider, GroundedAnswerGenerator
from rag_system.generation.prompts import INSUFFICIENT_CONTEXT
from rag_system.schemas import DocumentChunk, RetrievedChunk


class FakeAnswerProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return self.response


def source() -> RetrievedChunk:
    return RetrievedChunk(
        chunk=DocumentChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="annual-report.pdf",
            chunk_index=0,
            text="Revenue increased by 10 percent in 2024.",
            token_count=7,
            chunking_strategy="fixed_token",
            page_numbers=(12,),
            section_titles=("Results",),
        ),
        score=0.9,
    )


def test_generator_returns_answer_with_only_explicit_valid_citations() -> None:
    provider = FakeAnswerProvider("Revenue increased by 10 percent in 2024. [S1]")

    result = GroundedAnswerGenerator(provider).answer("How did revenue change?", (source(),))

    assert result.insufficient_context is False
    assert result.citations[0].document_name == "annual-report.pdf"
    assert result.citations[0].page_numbers == (12,)
    assert "Do not add facts not supported" in provider.prompt
    assert "[S1]" in provider.prompt


def test_generator_returns_insufficient_context_without_sources_or_citations() -> None:
    no_sources = GroundedAnswerGenerator(FakeAnswerProvider("unused")).answer("Question", ())
    unsupported = GroundedAnswerGenerator(FakeAnswerProvider("An unsupported answer")).answer(
        "Question", (source(),)
    )

    assert no_sources.text == INSUFFICIENT_CONTEXT
    assert no_sources.insufficient_context is True
    assert unsupported.text == INSUFFICIENT_CONTEXT
    assert unsupported.citations == ()


def test_generator_honors_the_model_insufficient_context_signal() -> None:
    result = GroundedAnswerGenerator(FakeAnswerProvider(INSUFFICIENT_CONTEXT)).answer(
        "Question", (source(),)
    )
    assert result == type(result)(INSUFFICIENT_CONTEXT, (), True)


def test_gemini_answer_provider_requires_an_api_key() -> None:
    with pytest.raises(ValueError):
        GeminiAnswerProvider("", "gemini-3.1-flash-lite")
