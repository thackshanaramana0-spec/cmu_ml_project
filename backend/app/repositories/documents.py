"""Document and ingestion-job data access."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, IngestionJob


def create_document(
    db: Session,
    *,
    user_id: uuid.UUID,
    filename: str,
    document_type: str,
    storage_path: str,
    course_name: str | None,
    tags: list[str],
) -> Document:
    doc = Document(
        user_id=user_id,
        filename=filename,
        document_type=document_type,
        storage_path=storage_path,
        course_name=course_name,
        tags=tags,
        status="pending",
    )
    db.add(doc)
    db.flush()  # populate doc.id before creating the job
    job = IngestionJob(document_id=doc.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: uuid.UUID) -> Document | None:
    return db.get(Document, document_id)


def list_documents(db: Session, user_id: uuid.UUID) -> list[Document]:
    stmt = (
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.upload_date.desc())
    )
    return list(db.scalars(stmt))


def latest_job(db: Session, document_id: uuid.UUID) -> IngestionJob | None:
    stmt = (
        select(IngestionJob)
        .where(IngestionJob.document_id == document_id)
        .order_by(IngestionJob.created_at.desc())
    )
    return db.scalars(stmt).first()


def set_document_status(
    db: Session, document_id: uuid.UUID, status: str, chunk_count: int | None = None
) -> None:
    doc = db.get(Document, document_id)
    if doc is None:
        return
    doc.status = status
    if chunk_count is not None:
        doc.chunk_count = chunk_count
    db.commit()


def set_job_status(
    db: Session, document_id: uuid.UUID, status: str, error: str | None = None
) -> None:
    job = latest_job(db, document_id)
    if job is None:
        return
    job.status = status
    job.error = error
    db.commit()


def delete_document(db: Session, document_id: uuid.UUID) -> None:
    doc = db.get(Document, document_id)
    if doc is not None:
        db.delete(doc)
        db.commit()
