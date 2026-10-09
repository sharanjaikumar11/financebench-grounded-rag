"""Optional local cross-encoder ranking, independent of embeddings."""

from __future__ import annotations

import math
from typing import Protocol

from rag_system.schemas import RetrievedChunk


class Reranker(Protocol):
    def rerank(
        self, query: str, candidates: tuple[RetrievedChunk, ...], top_k: int
    ) -> tuple[RetrievedChunk, ...]: ...


class CrossEncoderReranker:
    """Load an explicitly configured local model; never download during a query."""

    def __init__(self, model_name: str, batch_size: int = 8) -> None:
        if not model_name.strip() or batch_size < 1:
            raise ValueError("A reranker model and positive batch size are required")
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None

    def rerank(
        self, query: str, candidates: tuple[RetrievedChunk, ...], top_k: int
    ) -> tuple[RetrievedChunk, ...]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if not candidates:
            return ()
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, local_files_only=True)
        scores = self._model.predict(
            [(query, item.chunk.text) for item in candidates],
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        if len(scores) != len(candidates) or any(not math.isfinite(float(s)) for s in scores):
            raise RuntimeError("Reranker returned invalid scores")
        order = sorted(range(len(candidates)), key=lambda i: float(scores[i]), reverse=True)
        return tuple(RetrievedChunk(candidates[i].chunk, float(scores[i])) for i in order[:top_k])
