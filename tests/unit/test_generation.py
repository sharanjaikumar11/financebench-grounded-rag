import pytest

from rag_system.generation.answering import (
    GeminiAnswerProvider,
    GroundedAnswerGenerator,
)
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
    assert "only when the sources lack the facts" in provider.prompt
    assert "Financial-statement tables are evidence" in provider.prompt
    assert "capital expenditure/capital spending" in provider.prompt
    assert "highest, lowest, largest, or smallest" in provider.prompt
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


def test_gemini_answer_provider_converts_provider_errors_to_safe_runtime_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys
    from types import ModuleType, SimpleNamespace

    class ProviderUnavailableError(Exception):
        """A simulated provider failure."""

    class FailingModels:
        def generate_content(self, **_: object) -> None:
            raise ProviderUnavailableError("503 unavailable")

    fake_types = SimpleNamespace(
        GenerateContentConfig=lambda **kwargs: kwargs,
        ThinkingConfig=lambda **kwargs: kwargs,
    )
    fake_google = ModuleType("google")
    fake_google.genai = SimpleNamespace(Client=lambda **_: SimpleNamespace(models=FailingModels()))
    fake_genai = ModuleType("google.genai")
    fake_genai.types = fake_types
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        GeminiAnswerProvider("test-key", "gemini-3.1-flash-lite").generate("question")


def test_gemini_answer_provider_uses_fallback_after_a_capacity_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys
    from types import ModuleType, SimpleNamespace

    class CapacityError(Exception):
        """A simulated 503 provider response."""

    class Models:
        def __init__(self) -> None:
            self.models: list[str] = []

        def generate_content(self, **kwargs: object) -> SimpleNamespace:
            self.models.append(str(kwargs["model"]))
            if len(self.models) == 1:
                raise CapacityError("503 unavailable")
            return SimpleNamespace(text="Grounded answer [S1]")

    models = Models()
    fake_types = SimpleNamespace(
        GenerateContentConfig=lambda **kwargs: kwargs,
        ThinkingConfig=lambda **kwargs: kwargs,
    )
    fake_google = ModuleType("google")
    fake_google.genai = SimpleNamespace(Client=lambda **_: SimpleNamespace(models=models))
    fake_genai = ModuleType("google.genai")
    fake_genai.types = fake_types
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    provider = GeminiAnswerProvider(
        "test-key", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"
    )

    assert provider.generate("question") == "Grounded answer [S1]"
    assert models.models == ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]
