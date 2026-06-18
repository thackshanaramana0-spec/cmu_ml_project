"""Ingestion pipeline: extract -> chunk -> embed -> upsert to Qdrant.

This is the orchestrating function the background worker calls. It owns its own
DB session because it runs outside the request lifecycle. All failures mark the
document/job as failed with the error recorded, so nothing silently hangs in
"processing".
"""
from __future__ import annotations

import uuid
from pathlib import Path

from app.db import SessionLocal
from app.ingestion.chunker import chunk_text
from app.ingestion.extractors import extract_text
from app.providers.embedding_provider import get_embedding_provider
from app.repositories import documents as doc_repo
from app.retrieval import qdrant_store


def ingest_document(document_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        doc = doc_repo.get_document(db, document_id)
        if doc is None:
            return

        doc_repo.set_document_status(db, document_id, "processing")
        doc_repo.set_job_status(db, document_id, "running")

        text = extract_text(Path(doc.storage_path), doc.document_type)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No extractable text found in document")

        vectors = get_embedding_provider().embed(chunks)
        qdrant_store.upsert_chunks(
            user_id=doc.user_id,
            document_id=doc.id,
            source_type="document",
            course_name=doc.course_name,
            tags=doc.tags,
            chunks=chunks,
            vectors=vectors,
        )

        doc_repo.set_document_status(db, document_id, "ready", chunk_count=len(chunks))
        doc_repo.set_job_status(db, document_id, "done")
    except Exception as exc:  # noqa: BLE001 — surface any failure to the job row
        doc_repo.set_document_status(db, document_id, "failed")
        doc_repo.set_job_status(db, document_id, "error", error=str(exc))
    finally:
        db.close()
