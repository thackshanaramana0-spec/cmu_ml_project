import ChatSidebar from "@/components/ChatSidebar";

// The sidebar lives in the layout so it stays mounted (and keeps scroll/state)
// while navigating between /chat and /chat/<id>. Height fills below the root nav.
export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex h-[calc(100vh-65px)] max-w-5xl">
      <ChatSidebar />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
