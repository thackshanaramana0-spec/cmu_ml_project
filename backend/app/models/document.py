"""Document and ingestion-job models.

Chunk text and vectors live in Qdrant, not here — Postgres only owns document
metadata and processing state. `extra_metadata` (column name "metadata") is a
JSON bag so new metadata fields can be added later without a migration.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, utcnow, uuid_pk

# Status values are kept as plain strings (portable across SQLite/Postgres).
DOC_STATUS = ("pending", "processing", "ready", "failed")
JOB_STATUS = ("queued", "running", "done", "error")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)

    filename: Mapped[str] = mapped_column(String)
    document_type: Mapped[str] = mapped_column(String)  # pdf|pptx|docx|txt|md
    course_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String, default="pending")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String)

    # Attribute is renamed because `metadata` is reserved on the declarative base.
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    upload_date: Mapped[datetime] = created_at_col()

    jobs: Mapped[list["IngestionJob"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id"), index=True
    )
    status: Mapped[str] = mapped_column(String, default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    document: Mapped["Document"] = relationship(back_populates="jobs")
