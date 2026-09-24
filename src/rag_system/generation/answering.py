"""Grounded answer generation from retrieved document chunks."""

from __future__ import annotations

import re
from typing import Protocol

from rag_system.generation.citations import build_source_map, citations_from_answer
from rag_system.generation.prompts import (
    INSUFFICIENT_CONTEXT,
    grounded_answer_prompt,
    grounded_answer_retry_prompt,
)
from rag_system.retrieval.retriever import retrieval_query
from rag_system.schemas import GroundedAnswer, RetrievedChunk


class AnswerProvider(Protocol):
    """Produces text for a fully constructed grounded-answer prompt."""

    def generate(self, prompt: str) -> str: ...


class GeminiAnswerProvider:
    """Gemini-backed answer provider, initialized only when used."""

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_model: str | None = None,
        thinking_level: str = "low",
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required for answer generation")
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model if fallback_model != model else None
        self.thinking_level = thinking_level
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
        config = {"temperature": 0, "max_output_tokens": 256}
        if model.startswith("gemini-3"):
            config["thinking_config"] = types.ThinkingConfig(thinking_level=self.thinking_level)
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


class GroqAnswerProvider:
    """Groq-backed answer provider, initialized only when selected."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("A Groq API key is required for answer generation")
        self.api_key = api_key
        self.model = model
        self._client: object | None = None

    def generate(self, prompt: str) -> str:
        try:
            if self._client is None:
                from groq import Groq

                self._client = Groq(api_key=self.api_key)
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                # GPT-OSS otherwise returns reasoning separately and can spend a
                # small completion budget before producing its cited final answer.
                include_reasoning=False,
                reasoning_effort="low",
                max_completion_tokens=512,
            )
            text = completion.choices[0].message.content
        except Exception as error:
            raise RuntimeError(
                "Groq answer generation failed. Please verify GROQ_API_KEY, the configured model, and retry."
            ) from error
        if not text:
            raise RuntimeError("Groq returned an empty answer")
        return text.strip()


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

        source_map = build_source_map(_generation_evidence_sources(question, sources))
        response = self.provider.generate(grounded_answer_prompt(question, source_map)).strip()
        if response == INSUFFICIENT_CONTEXT:
            response = self.provider.generate(grounded_answer_retry_prompt(question, source_map)).strip()
            if response == INSUFFICIENT_CONTEXT:
                return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)

        citations = citations_from_answer(response, source_map)
        if not citations:
            return GroundedAnswer(INSUFFICIENT_CONTEXT, (), True)
        return GroundedAnswer(response, citations, False)


def _generation_evidence_sources(
    question: str, sources: tuple[RetrievedChunk, ...], maximum_sources: int = 9
) -> tuple[RetrievedChunk, ...]:
    """Keep the most answer-bearing retrieved chunks prominent for generation.

    Retrieval intentionally adds neighboring chunks to preserve table context. For
    answer generation, prioritize the chunks whose text covers the question and
    its standard financial-statement aliases, while retaining the full default
    expanded retrieval set for headers and supporting context. Nine 200-token
    chunks remain a compact evidence package while avoiding loss of a table's
    period header, unit, or direct value row.
    """
    if maximum_sources < 1:
        raise ValueError("maximum_sources must be at least one")
    expanded_question = retrieval_query(question)
    ranked = sorted(
        enumerate(sources),
        key=lambda item: (_generation_evidence_score(item[1].chunk.text, expanded_question), -item[0]),
        reverse=True,
    )
    return tuple(item for _, item in ranked[:maximum_sources])


def _generation_evidence_score(text: str, query: str) -> float:
    """Score a chunk by financial-term coverage and table-value signals."""
    stop_words = {
        "amount", "answer", "based", "does", "following", "from", "give", "have", "highest",
        "its", "million", "millions", "question", "shown", "that", "the", "this", "using", "was",
        "what", "which", "with", "year", "years", "usd", "fiscal",
    }
    terms = {
        _term_stem(term)
        for term in re.findall(r"[A-Za-z]+", query.casefold())
        if len(term) > 2 and term.casefold() not in stop_words
    }
    text_terms = {_term_stem(term) for term in re.findall(r"[A-Za-z]+", text.casefold())}
    coverage = len(terms & text_terms) / len(terms) if terms else 0.0
    numeric_density = min(len(re.findall(r"\b\d[\d,().%$-]*\b", text)), 8) / 40
    table_signal = bool(
        re.search(
            r"\b(?:consolidated|statement|balance\s+sheet|cash\s+flow|total\s+assets|net\s+income|"
            r"property,?\s+plant|notional\s+value)\b",
            text,
            flags=re.IGNORECASE,
        )
    )
    return coverage + numeric_density + (0.35 if table_signal else 0.0)


def _term_stem(term: str) -> str:
    if term.endswith("ies") and len(term) > 4:
        return term[:-3] + "y"
    if term.endswith("s") and not term.endswith("ss") and len(term) > 3:
        return term[:-1]
    return term
