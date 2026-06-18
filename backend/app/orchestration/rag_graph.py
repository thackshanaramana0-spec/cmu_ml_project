"""RAG chat as a LangGraph pipeline.

Flow:  retrieve -> grade -> (generate | refuse)

The `grade` node is what enforces the product rule "do not answer from model
knowledge if retrieval fails": if there are no hits, or the best similarity is
below the threshold, we route to `refuse` and return the fixed message instead
of calling the LLM. Single-agent by design (no multi-agent), but expressed as a
graph so future nodes (rerank, self-heal, hallucination-check) slot in cleanly.
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import get_settings
from app.providers.llm_provider import get_llm_provider
from app.retrieval.retriever import RetrievedChunk, retrieve

REFUSAL = "I could not find enough information in your uploaded materials."

SYSTEM_PROMPT = (
    "You are Academic Copilot, a study assistant that answers strictly from a "
    "student's uploaded course materials. Use ONLY the information in the provided "
    "context snippets. Cite the snippets you use with bracketed numbers like [1], "
    "[2]. If the context does not contain enough information to answer the "
    f'question, reply exactly with: "{REFUSAL}" '
    "Never use outside knowledge or guess."
)


class RagState(TypedDict, total=False):
    question: str
    user_id: uuid.UUID
    course_name: str | None
    hits: list[RetrievedChunk]
    grounded: bool
    answer: str
    sources: list[dict]


def _retrieve_node(state: RagState) -> RagState:
    hits = retrieve(
        user_id=state["user_id"],
        query=state["question"],
        course_name=state.get("course_name"),
        source_types=["document"],
    )
    return {"hits": hits}


def _grade_node(state: RagState) -> RagState:
    """Keep only chunks above the relevance threshold.

    The LLM should only see (and we should only cite) chunks that are actually
    relevant — otherwise low-score, unrelated chunks become misleading sources.
    `grounded` is true when at least one chunk survives.
    """
    settings = get_settings()
    relevant = [
        h for h in state.get("hits", []) if h.score >= settings.rag_score_threshold
    ]
    return {"hits": relevant, "grounded": bool(relevant)}


def _build_context(hits: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{i}] {h.text}" for i, h in enumerate(hits, start=1))


def _generate_node(state: RagState) -> RagState:
    hits = state["hits"]
    context = _build_context(hits)
    user_prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {state['question']}\n\n"
        "Answer the question using only the context above, citing sources as [n]:"
    )
    answer = get_llm_provider().chat(system=SYSTEM_PROMPT, user=user_prompt)

    sources = [
        {
            "number": i,
            "document_id": h.document_id,
            "chunk_index": h.chunk_index,
            "score": round(h.score, 4),
        }
        for i, h in enumerate(hits, start=1)
    ]
    return {"answer": answer.strip(), "sources": sources}


def _refuse_node(state: RagState) -> RagState:
    return {"answer": REFUSAL, "sources": []}


def _route(state: RagState) -> str:
    return "generate" if state.get("grounded") else "refuse"


@lru_cache
def get_rag_graph():
    """Compile the graph once and reuse it (nodes are stateless)."""
    graph = StateGraph(RagState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("grade", _grade_node)
    graph.add_node("generate", _generate_node)
    graph.add_node("refuse", _refuse_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade", _route, {"generate": "generate", "refuse": "refuse"}
    )
    graph.add_edge("generate", END)
    graph.add_edge("refuse", END)
    return graph.compile()


def answer_question(
    *, user_id: uuid.UUID, question: str, course_name: str | None = None
) -> tuple[str, list[dict]]:
    """Run the RAG graph and return (answer, sources)."""
    result: RagState = get_rag_graph().invoke(
        {"question": question, "user_id": user_id, "course_name": course_name}
    )
    return result["answer"], result.get("sources", [])
