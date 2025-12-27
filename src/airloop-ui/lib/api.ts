// Helper to call the server
export async function callChatAPI(message: string, conversationId: string) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, message }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat API error: ${res.status} ${text}`);
  }

  return res.json();
}
