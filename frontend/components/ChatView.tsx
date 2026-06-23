"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Source, getSession, sendChat } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[] | null;
}

export default function ChatView({ sessionId }: { sessionId: string | null }) {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load this session's history (or reset to empty for a new chat) whenever the
  // active session changes. History lives in the backend, so navigating here
  // restores the full conversation.
  useEffect(() => {
    let cancelled = false;
    if (!sessionId) {
      setMessages([]);
      return;
    }
    getSession(sessionId)
      .then((s) => {
        if (cancelled) return;
        setMessages(
          s.messages.map((m) => ({
            role: m.role,
            content: m.content,
            sources: m.sources,
          })),
        );
      })
      .catch(() => {
        // Unknown/!owned session — fall back to a new chat.
        if (!cancelled) router.replace("/chat");
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setError(null);
    setLoading(true);
    try {
      const res = await sendChat(text, sessionId);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
      // New chat just got an id — reflect it in the URL so refresh/tab-switch
      // restores it. The [sessionId] page reloads identical content from the DB.
      if (!sessionId) {
        router.replace(`/chat/${res.session_id}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col px-6 py-6">
      <div className="flex-1 space-y-4 overflow-y-auto pb-4">
        {messages.length === 0 && !loading && (
          <p className="mt-8 text-center text-sm text-neutral-400">
            Ask a question about your uploaded materials.
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                msg.role === "user"
                  ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900"
                  : "bg-white text-neutral-900 ring-1 ring-neutral-200 dark:bg-neutral-900 dark:text-neutral-100 dark:ring-neutral-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 border-t border-neutral-200 pt-2 dark:border-neutral-800">
                  <p className="mb-1 text-xs font-semibold text-neutral-400">Sources</p>
                  <ul className="space-y-0.5">
                    {msg.sources.map((s) => (
                      <li key={s.number} className="text-xs text-neutral-500">
                        [{s.number}] {s.filename ?? s.document_id} · chunk{" "}
                        {s.chunk_index} · {(s.score * 100).toFixed(0)}% match
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-white px-4 py-2.5 text-sm text-neutral-400 ring-1 ring-neutral-200 dark:bg-neutral-900 dark:ring-neutral-800">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your materials…"
          disabled={loading}
          className="flex-1 rounded-full border border-neutral-300 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-neutral-500 disabled:opacity-50 dark:border-neutral-700"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="rounded-full bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-40 dark:bg-neutral-100 dark:text-neutral-900"
        >
          Send
        </button>
      </form>
    </div>
  );
}
