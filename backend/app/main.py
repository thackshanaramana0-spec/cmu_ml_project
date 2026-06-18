"""FastAPI application entrypoint.

On startup we create tables (create_all is fine for the MVP; Alembic can be
introduced later), ensure the Qdrant collection exists, and seed the owner.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import SessionLocal, engine
from app.models import Base
from app.repositories.users import get_or_create_owner
from app.retrieval import qdrant_store
from app.routers import chat, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    qdrant_store.ensure_collection()
    with SessionLocal() as db:
        get_or_create_owner(db)
    yield


app = FastAPI(title="Academic Copilot", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
