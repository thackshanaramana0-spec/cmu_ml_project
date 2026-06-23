"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { SessionSummary, listSessions } from "@/lib/api";

export default function ChatSidebar() {
  const pathname = usePathname();
  const params = useParams();
  const activeId = (params?.sessionId as string | undefined) ?? null;
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  // Refetch whenever the route changes, so a session created after the first
  // message of a new chat shows up automatically.
  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setSessions([]));
  }, [pathname]);

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-neutral-200 dark:border-neutral-800">
      <div className="p-3">
        <Link
          href="/chat"
          className="block rounded-lg border border-neutral-300 px-3 py-2 text-center text-sm font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-900"
        >
          + New chat
        </Link>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
        {sessions.length === 0 ? (
          <p className="px-2 py-4 text-xs text-neutral-400">No chats yet.</p>
        ) : (
          sessions.map((s) => (
            <Link
              key={s.id}
              href={`/chat/${s.id}`}
              className={`block truncate rounded-lg px-3 py-2 text-sm ${
                s.id === activeId
                  ? "bg-neutral-200 font-medium dark:bg-neutral-800"
                  : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-900"
              }`}
              title={s.title}
            >
              {s.title}
            </Link>
          ))
        )}
      </nav>
    </aside>
  );
}
