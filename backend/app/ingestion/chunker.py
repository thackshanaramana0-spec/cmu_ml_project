"""Character-based chunker with overlap.

A simple, dependency-free splitter is the right altitude for the MVP: it splits
on paragraph boundaries first, then packs paragraphs into ~chunk_size windows
with a fixed overlap so context isn't lost across chunk borders. We can swap in a
smarter (token-aware / semantic) splitter later behind this same function.
"""
from __future__ import annotations

import re

from app.config import get_settings


def _split_paragraphs(text: str) -> list[str]:
    # Collapse runs of blank lines into paragraph breaks.
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    settings = get_settings()
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # If a single paragraph is larger than chunk_size, hard-split it.
        if len(para) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i : i + chunk_size])
            continue

        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            # Start the next window with a tail of the previous one for overlap.
            tail = current[-overlap:] if overlap and current else ""
            current = f"{tail}\n\n{para}" if tail else para

    if current:
        chunks.append(current)

    return [c.strip() for c in chunks if c.strip()]
