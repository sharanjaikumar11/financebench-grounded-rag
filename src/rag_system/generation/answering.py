"""Grounded answer generation from retrieved document chunks."""

from __future__ import annotations

from typing import Protocol

from rag_system.generation.citations import build_source_map, citations_from_answer
from rag_system.generation.prompts import (
    INSUFFICIENT_CONTEXT,
    grounded_answer_prompt,
    grounded_answer_retry_prompt,
)
from rag_system.schemas import GroundedAnswer, RetrievedChunk


class AnswerProvider(Protocol):
    """Produces text for a fully constructed grounded-answer prompt."""

    def generate(self, prompt: str) -> str: ...


class GeminiAnswerProvider:
    """Gemini-backed answer provider, initialized only when used."""

    def __init__(self, api_key: str, model: str, fallback_model: str | None = None) -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required for answer generation")
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model if fallback_model != model else None
        self._client: object | None = None

    def generate(self, prompt: str) -> str:
        from google import genai
        from google.genai import types

        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        try:
            response = self._generate(prompt, self.model, types)
        except Exception as error:
            if self.fallback_model and self._is_capacity_error(error):
                try:
                    response = self._generate(prompt, self.fallback_model, types)
                except Exception as fallback_error:
                    raise self._unavailable_error(fallback_error) from fallback_error
            else:
                raise self._unavailable_error(error) from error
        if not response.text:
            raise RuntimeError("Gemini returned an empty answer")
        return response.text.strip()

    def _generate(self, prompt: str, model: str, types: object) -> object:
        config = {"temperature": 0, "max_output_tokens": 160}
        if model.startswith("gemini-3"):
            config["thinking_config"] = types.ThinkingConfig(thinking_level="minimal")
        return self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config),
        )

    @staticmethod
    def _is_capacity_error(error: Exception) -> bool:
        return getattr(error, "code", None) == 503 or "503" in str(error) or "UNAVAILABLE" in str(error)

    @staticmethod
    def _unavailable_error(error: Exception) -> RuntimeError:
        if GeminiAnswerProvider._is_capacity_error(error):
            return RuntimeError(
                "Gemini is temporarily unavailable due to high demand. "
                "Please retry this question in a moment."
            )
        return RuntimeError("Gemini answer generation failed. Please verify the configured model and retry.")


class UnavailableAnswerProvider:
    """Makes indexing usable without configuring an answer-generation key."""

    def generate(self, prompt: str) -> str:
        raise RuntimeError("Set GEMINI_API_KEY before asking questions")


class GroundedAnswerGenerator:
    """Enforce evidence-only answering and return structured source citations."""

    def __init__(self, provider: AnswerProvider) -> None:
        self.provider = provider

    def answer(self, question: str, sources: tuple[RetrievedChunk, ...]) -> GroundedAnswer:
        if not sources:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)

        source_map = build_source_map(sources)
        response = self.provider.generate(grounded_answer_prompt(question, source_map)).strip()
        if response == INSUFFICIENT_CONTEXT:
            response = self.provider.generate(grounded_answer_retry_prompt(question, source_map)).strip()
            if response == INSUFFICIENT_CONTEXT:
                return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)

        citations = citations_from_answer(response, source_map)
        if not citations:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)
        return GroundedAnswer(response, citations, False)
