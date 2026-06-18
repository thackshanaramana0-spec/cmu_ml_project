"""Qdrant vector store wrapper.

All vector reads/writes go through this module so the rest of the app never
touches the Qdrant client directly. Uses embedded on-disk mode by default
(no server); set QDRANT_URL to point at a real server later — no caller changes.

Payload schema per point:
    user_id, document_id, source_type, course_name, tags, chunk_index, text
This is what enables metadata-filtered retrieval (per-feature) and the
unfiltered cross-source search used by Academic Memory Search.
"""
from __future__ import annotations

import uuid
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.config import get_settings


@lru_cache
def get_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    # Embedded, on-disk persistence — no server required.
    return QdrantClient(path=settings.qdrant_path)


def ensure_collection() -> None:
    """Create the collection if missing. Safe to call on every startup."""
    settings = get_settings()
    client = get_client()
    if client.collection_exists(settings.qdrant_collection):
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qm.VectorParams(
            size=settings.embedding_dim, distance=qm.Distance.COSINE
        ),
    )


def upsert_chunks(
    *,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    source_type: str,
    course_name: str | None,
    tags: list[str],
    chunks: list[str],
    vectors: list[list[float]],
) -> int:
    """Upsert one point per chunk. Returns the number of points written."""
    settings = get_settings()
    client = get_client()
    points = [
        qm.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "user_id": str(user_id),
                "document_id": str(document_id),
                "source_type": source_type,
                "course_name": course_name,
                "tags": tags,
                "chunk_index": idx,
                "text": chunk,
            },
        )
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
    ]
    if points:
        client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def delete_by_document(document_id: uuid.UUID) -> None:
    settings = get_settings()
    client = get_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="document_id",
                        match=qm.MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
    )
