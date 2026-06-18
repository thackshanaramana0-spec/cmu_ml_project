"""Pydantic request/response schemas for the documents API."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    document_type: str
    course_name: str | None
    tags: list[str]
    status: str
    chunk_count: int
    upload_date: datetime


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    error: str | None


class DocumentDetail(DocumentOut):
    job: JobOut | None = None


class UploadAccepted(BaseModel):
    document_id: uuid.UUID
    status: str
