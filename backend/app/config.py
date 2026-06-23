"""Application configuration.

Single source of truth for runtime settings, loaded from environment / .env.
Everything that might change between machines or future deployments (DB, vector
store, model names, chunking) lives here so the rest of the code never hardcodes
infrastructure details.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env to an absolute path (backend/.env) based on this file's location,
# NOT the process working directory. Under `uvicorn --reload` the worker's cwd is
# not guaranteed, and a cwd-relative ".env" can silently miss, falling back to the
# SQLite default — which previously caused the app to run on the wrong database.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # Owner (no auth in the MVP; this identity is seeded as the single owner)
    app_owner_email: str = "owner@localhost"
    app_owner_name: str = "Owner"

    # Database
    database_url: str = "sqlite:///./academic_copilot.db"

    # Qdrant: embedded on-disk mode when qdrant_url is empty
    qdrant_url: str = ""
    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "academic_chunks"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    llm_model: str = "qwen2.5:14b"

    # Ingestion
    upload_dir: str = "./uploads"
    max_upload_mb: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # Retrieval / RAG
    rag_top_k: int = 5
    # Minimum cosine similarity for a hit to count as relevant. Below this for
    # the best hit, the system refuses rather than answering from model knowledge.
    rag_score_threshold: float = 0.5
    llm_temperature: float = 0.2


@lru_cache
def get_settings() -> Settings:
    return Settings()
