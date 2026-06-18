"""Document service: business logic for upload and deletion.

Routers stay thin (HTTP only); this layer owns file persistence, validation
decisions, and coordination between the repository, the vector store, and the
ingestion worker.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.ingestion.extractors import detect_type
from app.repositories import documents as doc_repo
from app.retrieval import qdrant_store


class UploadError(ValueError):
    """Raised for client-correctable upload problems (bad type, too big)."""


def save_upload(
    db: Session,
    *,
    user_id: uuid.UUID,
    filename: str,
    content: bytes,
    course_name: str | None,
    tags: list[str],
):
    settings = get_settings()

    document_type = detect_type(filename)
    if document_type is None:
        raise UploadError(
            f"Unsupported file type for '{filename}'. "
            "Allowed: pdf, pptx, docx, txt, md."
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise UploadError(f"File exceeds the {settings.max_upload_mb} MB limit.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    # Store under a generated id to avoid collisions and path-traversal in names.
    stored_name = f"{uuid.uuid4()}_{Path(filename).name}"
    storage_path = upload_dir / stored_name
    storage_path.write_bytes(content)

    return doc_repo.create_document(
        db,
        user_id=user_id,
        filename=Path(filename).name,
        document_type=document_type,
        storage_path=str(storage_path),
        course_name=course_name,
        tags=tags,
    )


def delete_document(db: Session, document_id: uuid.UUID) -> bool:
    doc = doc_repo.get_document(db, document_id)
    if doc is None:
        return False
    # Vectors first, then the file, then the row — orphan-free even on partial failure.
    qdrant_store.delete_by_document(document_id)
    try:
        Path(doc.storage_path).unlink(missing_ok=True)
    except OSError:
        pass
    doc_repo.delete_document(db, document_id)
    return True
