"""LLM provider interface + Ollama chat implementation.

Mirrors EmbeddingProvider: a thin abstraction so the local Ollama model can be
swapped for a cloud LLM later without touching the orchestration graphs. The
optional `format_json` flag maps to Ollama's structured-output mode, which the
later quiz/flashcard phases rely on.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.config import get_settings


class LLMProvider(ABC):
    @abstractmethod
    def chat(
        self,
        *,
        system: str,
        user: str,
        format_json: bool = False,
        temperature: float | None = None,
    ) -> str:
        """Return the assistant message content for a single-turn prompt."""


class OllamaLLMProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.llm_model
        self._default_temperature = settings.llm_temperature

    def chat(
        self,
        *,
        system: str,
        user: str,
        format_json: bool = False,
        temperature: float | None = None,
    ) -> str:
        payload: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": (
                    temperature if temperature is not None else self._default_temperature
                )
            },
        }
        if format_json:
            payload["format"] = "json"

        # Generous timeout: local generation on a 14B model can take a while.
        with httpx.Client(timeout=300.0) as client:
            resp = client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["message"]["content"]


def get_llm_provider() -> LLMProvider:
    return OllamaLLMProvider()
