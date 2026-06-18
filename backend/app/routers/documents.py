"""Documents API (Feature 1: ingestion).

HTTP concerns only: parse the request, enforce the contract, delegate to the
service, shape the response. Ingestion runs as a background task so the upload
call returns immediately (202) while embedding happens out of band.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.deps import get_current_owner
from app.db import get_db
from app.ingestion.pipeline import ingest_document
from app.models import User
from app.repositories import documents as doc_repo
from app.schemas.document import DocumentDetail, DocumentOut, JobOut, UploadAccepted
from app.services import documents as doc_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


@router.post("", status_code=202, response_model=UploadAccepted)
def upload_document(
    background: BackgroundTasks,
    file: UploadFile,
    course_name: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> UploadAccepted:
    content = file.file.read()
    try:
        doc = doc_service.save_upload(
            db,
            user_id=owner.id,
            filename=file.filename or "upload",
            content=content,
            course_name=course_name,
            tags=_parse_tags(tags),
        )
    except doc_service.UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # In-process background ingestion. Swap for a real queue later without
    # touching this router.
    background.add_task(ingest_document, doc.id)
    return UploadAccepted(document_id=doc.id, status=doc.status)


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> list[DocumentOut]:
    return [DocumentOut.model_validate(d) for d in doc_repo.list_documents(db, owner.id)]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> DocumentDetail:
    doc = doc_repo.get_document(db, document_id)
    if doc is None or doc.user_id != owner.id:
        raise HTTPException(status_code=404, detail="Document not found")
    job = doc_repo.latest_job(db, document_id)
    detail = DocumentDetail.model_validate(doc)
    detail.job = JobOut.model_validate(job) if job else None
    return detail


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> None:
    doc = doc_repo.get_document(db, document_id)
    if doc is None or doc.user_id != owner.id:
        raise HTTPException(status_code=404, detail="Document not found")
    doc_service.delete_document(db, document_id)
