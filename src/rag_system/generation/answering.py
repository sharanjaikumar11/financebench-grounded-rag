"""Grounded answer generation from retrieved document chunks."""

from __future__ import annotations

from typing import Protocol

from rag_system.generation.citations import build_source_map, citations_from_answer
from rag_system.generation.prompts import INSUFFICIENT_CONTEXT, grounded_answer_prompt
from rag_system.schemas import GroundedAnswer, RetrievedChunk


class AnswerProvider(Protocol):
    """Produces text for a fully constructed grounded-answer prompt."""

    def generate(self, prompt: str) -> str: ...


class GeminiAnswerProvider:
    """Gemini-backed answer provider, initialized only when used."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required for answer generation")
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        from google import genai

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(model=self.model, contents=prompt)
        if not response.text:
            raise RuntimeError("Gemini returned an empty answer")
        return response.text.strip()


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
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)

        citations = citations_from_answer(response, source_map)
        if not citations:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)
        return GroundedAnswer(response, citations, False)
