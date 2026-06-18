"""Retrieval: embed a query and fetch the most relevant chunks from Qdrant.

Kept separate from the orchestration graph so that a future "self-healing RAG"
upgrade can wrap/extend retrieval (re-query, rerank) without changing the graph
or services.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from qdrant_client.http import models as qm

from app.config import get_settings
from app.providers.embedding_provider import get_embedding_provider
from app.retrieval import qdrant_store


@dataclass
class RetrievedChunk:
    text: str
    score: float
    document_id: str
    chunk_index: int
    source_type: str
    course_name: str | None


def retrieve(
    *,
    user_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
    course_name: str | None = None,
    source_types: list[str] | None = None,
) -> list[RetrievedChunk]:
    """Return the top-k chunks for a query, filtered to the owner's data.

    `source_types` lets callers scope the search (e.g. only documents); when None,
    all source types are searched — which is what Academic Memory Search will use.
    """
    settings = get_settings()
    top_k = top_k or settings.rag_top_k

    query_vector = get_embedding_provider().embed([query])[0]

    must: list[qm.FieldCondition] = [
        qm.FieldCondition(key="user_id", match=qm.MatchValue(value=str(user_id)))
    ]
    if course_name:
        must.append(
            qm.FieldCondition(
                key="course_name", match=qm.MatchValue(value=course_name)
            )
        )
    if source_types:
        must.append(
            qm.FieldCondition(
                key="source_type", match=qm.MatchAny(any=source_types)
            )
        )

    client = qdrant_store.get_client()
    result = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=qm.Filter(must=must),
        limit=top_k,
        with_payload=True,
    )

    chunks: list[RetrievedChunk] = []
    for point in result.points:
        payload = point.payload or {}
        chunks.append(
            RetrievedChunk(
                text=payload.get("text", ""),
                score=point.score,
                document_id=payload.get("document_id", ""),
                chunk_index=payload.get("chunk_index", -1),
                source_type=payload.get("source_type", "document"),
                course_name=payload.get("course_name"),
            )
        )
    return chunks
