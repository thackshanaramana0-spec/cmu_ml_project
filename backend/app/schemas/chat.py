"""Pydantic schemas for the chat API."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None
    course_name: str | None = None


class Source(BaseModel):
    number: int
    document_id: str
    filename: str | None = None
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    sources: list[Source]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str
    sources: list[Source] | None = None
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime


class SessionDetail(SessionOut):
    messages: list[MessageOut] = []
