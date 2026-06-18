"""Embedding provider interface + Ollama implementation.

The interface is the seam that lets us swap the local Ollama model for a cloud
embedding API (or fastembed) later without touching ingestion/retrieval code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.config import get_settings


class EmbeddingProvider(ABC):
    """Turns text into vectors. Implementations must be deterministic per model."""

    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning one vector per input (order preserved)."""


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.embedding_model
        self.dim = settings.embedding_dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Ollama's /api/embed accepts a batch ("input") and returns "embeddings".
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{self._base_url}/api/embed",
                json={"model": self._model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
        embeddings = data.get("embeddings")
        if not embeddings or len(embeddings) != len(texts):
            raise RuntimeError(
                f"Ollama returned {len(embeddings or [])} embeddings for "
                f"{len(texts)} inputs"
            )
        return embeddings


def get_embedding_provider() -> EmbeddingProvider:
    """Factory — single place that decides which implementation is active."""
    return OllamaEmbeddingProvider()
