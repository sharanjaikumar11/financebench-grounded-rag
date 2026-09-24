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


class SentenceTransformerEmbeddingProvider:
    """Local Sentence Transformer embeddings with no network fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: object | None = None

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, local_files_only=True)
        vectors = self._model.encode(list(texts), normalize_embeddings=True)
        return tuple(tuple(float(value) for value in vector) for vector in vectors)
