"""Chat service (Feature 2): orchestrates a RAG turn and persists it.

Responsibilities: resolve/create the session, save the user message, run the RAG
graph, enrich the returned sources with human-readable filenames, save the
assistant message, and hand back the result. The router stays HTTP-only.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document
from app.orchestration.rag_graph import answer_question
from app.repositories import chat as chat_repo


def _filename_map(db: Session, document_ids: list[str]) -> dict[str, str]:
    """Resolve document_id -> filename for the cited sources."""
    uuids: list[uuid.UUID] = []
    for did in set(document_ids):
        try:
            uuids.append(uuid.UUID(did))
        except (ValueError, TypeError):
            continue
    if not uuids:
        return {}
    rows = db.scalars(select(Document).where(Document.id.in_(uuids)))
    return {str(d.id): d.filename for d in rows}


def send_message(
    db: Session,
    *,
    user_id: uuid.UUID,
    message: str,
    session_id: uuid.UUID | None,
    course_name: str | None,
) -> tuple[uuid.UUID, str, list[dict]]:
    # Resolve or create the session (title seeded from the first message).
    if session_id is None:
        title = message.strip()[:40] or "New chat"
        session = chat_repo.create_session(db, user_id=user_id, title=title)
    else:
        session = chat_repo.get_session(db, session_id)
        if session is None or session.user_id != user_id:
            raise ValueError("Session not found")

    chat_repo.add_message(db, session_id=session.id, role="user", content=message)

    answer, sources = answer_question(
        user_id=user_id, question=message, course_name=course_name
    )

    # Enrich sources with filenames for display.
    fmap = _filename_map(db, [s["document_id"] for s in sources])
    for s in sources:
        s["filename"] = fmap.get(s["document_id"])

    chat_repo.add_message(
        db,
        session_id=session.id,
        role="assistant",
        content=answer,
        sources=sources or None,
    )
    return session.id, answer, sources
