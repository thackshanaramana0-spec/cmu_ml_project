"""Chat API (Feature 2: knowledge-base RAG chat)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_owner
from app.models import User
from app.repositories import chat as chat_repo
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SessionDetail,
    SessionOut,
)
from app.services import chat as chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def send_message(
    body: ChatRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> ChatResponse:
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        session_id, answer, sources = chat_service.send_message(
            db,
            user_id=owner.id,
            message=body.message,
            session_id=body.session_id,
            course_name=body.course_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChatResponse(session_id=session_id, answer=answer, sources=sources)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> list[SessionOut]:
    return [SessionOut.model_validate(s) for s in chat_repo.list_sessions(db, owner.id)]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_owner),
) -> SessionDetail:
    session = chat_repo.get_session(db, session_id)
    if session is None or session.user_id != owner.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail.model_validate(session)
