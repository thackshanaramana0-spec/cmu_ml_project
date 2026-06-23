import ChatView from "@/components/ChatView";

// An existing chat. ChatView loads this session's history from the backend.
// (In Next 15 route `params` is a Promise.)
export default async function SessionChatPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return <ChatView sessionId={sessionId} />;
}
