"""Database engine and session management (SQLAlchemy 2.0, sync).

Sync sessions keep the MVP simple: FastAPI runs `def` endpoints in a threadpool,
so we avoid async-driver complexity. The engine is created from DATABASE_URL, so
swapping SQLite -> Postgres is purely a config change.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# check_same_thread is a SQLite-only flag; harmless to compute conditionally.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
