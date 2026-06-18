# Academic Copilot

An AI-powered academic assistant (personal "second brain") for managing course
materials, chatting with documents, and generating study aids. Runs **locally**.

> Status: **Phase 3 — RAG Chat** complete. Phase 2 ingestion (upload → extract →
> chunk → embed → Qdrant) plus a LangGraph RAG pipeline (retrieve → grade →
> generate) that cites sources and refuses when retrieval confidence is low.
> Auth and Docker are intentionally deferred.

The frontend calls the backend directly via `NEXT_PUBLIC_API_URL`
(`frontend/.env.local`, default `http://localhost:8000`) rather than the dev
rewrite-proxy, because local LLM responses can exceed the proxy's connection
timeout. CORS for the frontend origin is enabled on the backend.

## Stack

- **Backend:** FastAPI + SQLAlchemy (Python 3.14)
- **DB:** SQLite by default (swap to Postgres via `DATABASE_URL`)
- **Vector store:** Qdrant in embedded on-disk mode (no server needed)
- **Embeddings + LLM:** Ollama (`nomic-embed-text`, `qwen2.5:14b`)
- **Frontend:** Next.js + TypeScript + Tailwind

## Prerequisites

- Python 3.12+ and Node 18+
- [Ollama](https://ollama.com) running, with the embedding model pulled:
  ```
  ollama pull nomic-embed-text
  ```

## One-time setup

```bash
# backend
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt # macOS/Linux
cp .env.example .env
cd ..

# frontend + root orchestrator
npm install --prefix frontend
npm install
```

## Run everything with one command

From the repo root:

```bash
npm run dev
```

This starts the FastAPI backend (`:8000`) and the Next.js frontend (`:3000`)
together with unified, color-coded output; Ctrl-C stops both.

- App: http://localhost:3000
- API docs: http://localhost:8000/docs · Health: http://localhost:8000/api/health

> **macOS/Linux:** the `dev:backend` script uses the Windows venv path
> (`.venv\Scripts\python.exe`). Change it to `.venv/bin/python` in the root
> `package.json`.

You can also run either side alone: `npm run dev:backend` or `npm run dev:frontend`.

## Switching to Postgres later

Set `DATABASE_URL` in `backend/.env`, e.g.:

```
DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost:5432/academic_copilot
```

Models use portable column types, so no code changes are needed. (`pip install
psycopg[binary]` for the driver.)
