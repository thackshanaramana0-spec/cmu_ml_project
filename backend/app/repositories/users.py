"""User data access.

Single responsibility: all Postgres/SQLite access for the User aggregate.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User


def get_or_create_owner(db: Session) -> User:
    """Return the single owner, creating it from config on first run.

    This is the no-auth stand-in for "current user". When OAuth is added, the
    owner row gains a google_sub instead of being seeded from config.
    """
    settings = get_settings()
    owner = db.scalars(select(User).where(User.is_owner.is_(True))).first()
    if owner is None:
        owner = User(
            email=settings.app_owner_email,
            display_name=settings.app_owner_name,
            is_owner=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
    return owner
