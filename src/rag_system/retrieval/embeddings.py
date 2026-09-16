"""Embedding providers used by dense retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Produces one dense vector per input text."""

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]: ...


class GeminiEmbeddingProvider:
    """Gemini-backed embedding provider, initialized only when used."""

    def __init__(self, api_key: str, model: str = "gemini-embedding-001") -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required for embeddings")
        self.api_key = api_key
        self.model = model

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()

        from google import genai

        client = genai.Client(api_key=self.api_key)
        response = client.models.embed_content(model=self.model, contents=list(texts))
        return tuple(tuple(item.values) for item in response.embeddings)
