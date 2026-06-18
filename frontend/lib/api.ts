// Typed client for the Academic Copilot backend.
//
// Calls go directly to the backend (NEXT_PUBLIC_API_URL, default
// http://localhost:8000). Direct calls matter because LLM responses can take
// 30-60s locally, and the Next.js dev rewrite-proxy drops long connections
// (socket hang up). CORS is enabled on the backend for the frontend origin.
// If NEXT_PUBLIC_API_URL is unset, API_BASE is "" and calls fall back to the
// same-origin rewrite proxy configured in next.config.ts.

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

const url = (path: string) => `${API_BASE}${path}`;

export type DocStatus = "pending" | "processing" | "ready" | "failed";

export interface DocumentOut {
  id: string;
  filename: string;
  document_type: string;
  course_name: string | null;
  tags: string[];
  status: DocStatus;
  chunk_count: number;
  upload_date: string;
}

export interface UploadAccepted {
  document_id: string;
  status: DocStatus;
}

export async function listDocuments(): Promise<DocumentOut[]> {
  const res = await fetch(url("/api/documents"), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load documents (${res.status})`);
  return res.json();
}

export async function uploadDocument(
  file: File,
  courseName: string,
  tags: string,
): Promise<UploadAccepted> {
  const form = new FormData();
  form.append("file", file);
  if (courseName.trim()) form.append("course_name", courseName.trim());
  if (tags.trim()) form.append("tags", tags.trim());

  const res = await fetch(url("/api/documents"), { method: "POST", body: form });
  if (!res.ok) {
    let detail = `Upload failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(url(`/api/documents/${id}`), { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Delete failed (${res.status})`);
  }
}

// ---- Chat (RAG) ----

export interface Source {
  number: number;
  document_id: string;
  filename: string | null;
  chunk_index: number;
  score: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: Source[];
}

export async function sendChat(
  message: string,
  sessionId: string | null,
): Promise<ChatResponse> {
  const res = await fetch(url("/api/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) {
    let detail = `Chat failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}
