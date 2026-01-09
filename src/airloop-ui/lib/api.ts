const API_BASE_URL = "http://127.0.0.1:8000";

// Helper to call the server
export async function callChatAPI(
  message: string,
  conversationId: string,
  userId?: number
) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      user_id: userId,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat API error: ${res.status} ${text}`);
  }

  return res.json();
}

export async function submitFeedback(traceId: string, score: number, comment?: string) {
  const res = await fetch(`${API_BASE_URL}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trace_id: traceId, score, comment }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Feedback API error: ${res.status} ${text}`);
  }

  return res.json();
}

export async function fetchSessions(limit: number = 20, userId?: number) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (userId !== undefined) {
    params.set("user_id", String(userId));
  }
  const res = await fetch(`${API_BASE_URL}/api/sessions?${params.toString()}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Sessions API error: ${res.status} ${text}`);
  }
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Login error: ${res.status} ${text}`);
  }
  return res.json();
}
