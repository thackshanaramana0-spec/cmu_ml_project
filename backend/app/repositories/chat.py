"""Chat session/message data access."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession


def create_session(db: Session, *, user_id: uuid.UUID, title: str) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: uuid.UUID) -> ChatSession | None:
    return db.get(ChatSession, session_id)


def list_sessions(db: Session, user_id: uuid.UUID) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
    )
    return list(db.scalars(stmt))


def add_message(
    db: Session,
    *,
    session_id: uuid.UUID,
    role: str,
    content: str,
    sources: list | None = None,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id, role=role, content=content, sources=sources
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_messages(db: Session, session_id: uuid.UUID) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return list(db.scalars(stmt))
