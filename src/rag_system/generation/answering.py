"""Grounded answer generation from retrieved document chunks."""

from __future__ import annotations

from typing import Protocol

from rag_system.generation.citations import build_source_map, citations_from_answer
from rag_system.generation.prompts import INSUFFICIENT_CONTEXT, grounded_answer_prompt
from rag_system.generation.table_calculations import TableCalculator
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
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty answer")
        return response.text.strip()


class UnavailableAnswerProvider:
    """Makes indexing usable without configuring an answer-generation key."""

    def generate(self, prompt: str) -> str:
        raise RuntimeError("Set GEMINI_API_KEY before asking questions")


class GroundedAnswerGenerator:
    """Enforce evidence-only answering and return structured source citations."""

    def __init__(self, provider: AnswerProvider, table_calculator: TableCalculator | None = None) -> None:
        self.provider = provider
        self.table_calculator = table_calculator or TableCalculator()

    def answer(self, question: str, sources: tuple[RetrievedChunk, ...]) -> GroundedAnswer:
        if not sources:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)

        source_map = build_source_map(sources)
        calculations = tuple(
            evidence.render() for evidence in self.table_calculator.evidence(question, source_map)
        )
        response = self.provider.generate(grounded_answer_prompt(question, source_map, calculations)).strip()
        if response == INSUFFICIENT_CONTEXT:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)

        citations = citations_from_answer(response, source_map)
        if not citations:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)
        return GroundedAnswer(response, citations, False)
