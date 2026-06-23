import ChatView from "@/components/ChatView";

// A new chat (no session yet). On the first message ChatView creates the session
// and redirects to /chat/<id>.
export default function NewChatPage() {
  return <ChatView sessionId={null} />;
}
