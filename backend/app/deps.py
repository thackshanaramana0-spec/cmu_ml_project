"""Shared FastAPI dependencies.

`get_current_owner` is the single seam where "who is the user" is resolved. Today
it returns the seeded owner (no auth); when Google OAuth lands, only this function
changes — routers stay identical.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.repositories.users import get_or_create_owner


def get_current_owner(db: Session = Depends(get_db)) -> User:
    return get_or_create_owner(db)
