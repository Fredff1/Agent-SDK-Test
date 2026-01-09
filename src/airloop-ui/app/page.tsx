"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Menu } from "lucide-react";
import { AgentPanel } from "@/components/agent-panel";
import { Chat } from "@/components/Chat";
import type { Agent, AgentEvent, GuardrailCheck, Message } from "@/lib/types";
import {
  callChatAPI,
  submitFeedback,
  fetchSessions,
  fetchOrders,
  createOrder,
} from "@/lib/api";

type Session = {
  id: string;
  title: string;
  conversationId: string | null;
  orderId: number | null;
  messages: Message[];
  events: AgentEvent[];
  agents: Agent[];
  currentAgent: string;
  guardrails: GuardrailCheck[];
  context: Record<string, any>;
  isLoading: boolean;
  initialized: boolean;
};

type Order = {
  id: number;
  confirmation_number: string;
  flight_number: string;
  seat_number: number;
  meal_selection?: string | null;
  status?: string;
};

const createSession = (title: string, order: Order): Session => ({
  id: Math.random().toString(36).slice(2),
  title,
  conversationId: null,
  orderId: order.id,
  messages: [],
  events: [],
  agents: [],
  currentAgent: "",
  guardrails: [],
  context: {
    order_id: order.id,
    confirmation_number: order.confirmation_number,
    flight_number: order.flight_number,
    seat_number: String(order.seat_number),
    order_status: order.status ?? "active",
  },
  isLoading: false,
  initialized: false,
});

const normalizeGuardrails = (raw: any[]): GuardrailCheck[] =>
  (raw || []).map((gr: any) => ({
    id: gr.id ?? Math.random().toString(36).slice(2),
    name: gr.name,
    input: gr.input,
    reasoning: gr.reasoning,
    passed: !!gr.passed,
    timestamp: gr.timestamp ? new Date(gr.timestamp) : new Date(),
  }));

export default function Home() {
  const router = useRouter();
  const [userId, setUserId] = useState<number | null>(null);
  const [userProfile, setUserProfile] = useState<{
    username: string;
    account_number?: string;
  } | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionCounter, setSessionCounter] = useState(1);
  const [isAgentPanelCollapsed, setIsAgentPanelCollapsed] = useState(false);
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);
  const [isOrdersLoading, setIsOrdersLoading] = useState(false);
  const [orderError, setOrderError] = useState("");
  const [isOrderPickerOpen, setIsOrderPickerOpen] = useState(false);
  const sessionsStorageKey = userId ? `airloop_sessions_v1_${userId}` : "airloop_sessions_v1";

  const getOrderStatus = (orderId: number | null) => {
    if (orderId == null) return undefined;
    return orders.find((item) => item.id === orderId)?.status;
  };

  useEffect(() => {
    const raw = localStorage.getItem("airloop_user");
    if (!raw) {
      router.replace("/login");
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      if (typeof parsed?.id === "number") {
        setUserId(parsed.id);
        setUserProfile({
          username: parsed.username ?? "User",
          account_number: parsed.account_number ?? undefined,
        });
        setIsAuthChecked(true);
        return;
      }
    } catch {
      // fall through
    }
    localStorage.removeItem("airloop_user");
    router.replace("/login");
  }, [router]);

  const loadOrders = async (uid: number) => {
    setIsOrdersLoading(true);
    setOrderError("");
    try {
      const data = await fetchOrders(uid);
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load orders", err);
      setOrderError("Failed to load orders.");
    } finally {
      setIsOrdersLoading(false);
    }
  };

  useEffect(() => {
    if (userId == null) return;
    loadOrders(userId);
  }, [userId]);

  useEffect(() => {
    if (orders.length === 0) return;
    setSessions((prev) =>
      prev.map((session) => {
        if (!session.orderId) return session;
        const status = getOrderStatus(session.orderId);
        if (!status || session.context?.order_status === status) return session;
        return {
          ...session,
          context: {
            ...session.context,
            order_status: status,
          },
        };
      })
    );
  }, [orders]);

  // Load sessions from API (persistent store) first; fallback to localStorage
  useEffect(() => {
    (async () => {
      try {
        if (userId == null) return;
        const apiSessions = await fetchSessions(50, userId);
        if (Array.isArray(apiSessions) && apiSessions.length > 0) {
          const restored: Session[] = apiSessions.map((s: any, idx: number) => ({
            id: s.conversation_id || `session-${idx}`,
            title: s.title || `Session ${idx + 1}`,
            conversationId: s.conversation_id || null,
            orderId: s.context?.order_id ?? null,
            messages: Array.isArray(s.messages)
              ? s.messages.map((m: any) => ({
                  id: m.id ?? `${s.conversation_id || idx}-${Math.random()}`,
                  content:
                    typeof m.content === "string"
                      ? m.content
                      : m.content != null
                      ? JSON.stringify(m.content)
                      : "",
                  role: m.role,
                  agent: m.agent,
                  traceId: m.traceId,
                  timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
                }))
              : [],
            events: Array.isArray(s.events)
              ? s.events.map((e: any) => ({
                  ...e,
                  timestamp: e.timestamp ? new Date(e.timestamp) : new Date(),
                }))
              : [],
            agents: Array.isArray(s.agents) ? s.agents : [],
            currentAgent: s.current_agent || "",
            guardrails: normalizeGuardrails(s.guardrails || []),
            context: {
              ...(s.context || {}),
              order_status: getOrderStatus(s.context?.order_id ?? null),
            },
            isLoading: false,
            initialized: true,
          }));
          setSessions(restored);
          setActiveSessionId(restored[0].id);
          setSessionCounter(restored.length);
          return;
        }
      } catch (err) {
        console.error("Failed to load sessions from API", err);
      }

      try {
        if (userId == null) return;
        const raw = localStorage.getItem(sessionsStorageKey);
        if (raw) {
          const parsed = JSON.parse(raw);
          const storedSessions: Session[] = (parsed.sessions || []).map((s: Session) => ({
            ...s,
            isLoading: false,
          }));
          if (storedSessions.length > 0) {
            setSessions(storedSessions);
            setActiveSessionId(parsed.activeSessionId || storedSessions[0].id);
            setSessionCounter(parsed.sessionCounter || storedSessions.length);
            return;
          }
        }
      } catch (err) {
        console.error("Failed to load sessions from storage", err);
      }
      setSessions([]);
      setActiveSessionId(null);
      setSessionCounter(0);
    })();
  }, [userId]);

  // Persist sessions to localStorage
  useEffect(() => {
    if (sessions.length === 0) return;
    try {
      localStorage.setItem(
        sessionsStorageKey,
        JSON.stringify({
          sessions,
          activeSessionId,
          sessionCounter,
        })
      );
    } catch (err) {
      console.error("Failed to persist sessions", err);
    }
  }, [sessions, activeSessionId, sessionCounter]);

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? sessions[0];
  const sessionOptions = sessions.map((session) => {
    const userChunks = session.messages
      .filter(
        (message) =>
          message.role === "user" && message.content !== "DISPLAY_SEAT_MAP"
      )
      .map((message) => message.content.replace(/\s+/g, " ").trim())
      .filter(Boolean);
    const normalized = userChunks.join(" / ").trim();
    const maxLength = 40;
    const chars = Array.from(normalized);
    const summary = chars.slice(0, maxLength).join("");
    const subtitle = normalized
      ? chars.length > maxLength
        ? `${summary}...`
        : summary
      : "暂无摘要";
    return {
      id: session.id,
      title: session.title,
      subtitle,
    };
  });

  // Boot the conversation for new sessions only
  useEffect(() => {
    if (!activeSessionId) return;
    const session = sessions.find((s) => s.id === activeSessionId);
    if (!session || session.initialized || session.isLoading) return;
    if (userId == null || session.orderId == null) return;

    const bootSession = async (sessionId: string) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId ? { ...s, isLoading: true } : s
      )
    );
      let data: any = null;
      try {
        data = await callChatAPI("", "", userId, session.orderId ?? undefined);
      } catch (err) {
        console.error("Failed to start conversation", err);
      }
      if (!data) {
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId ? { ...s, isLoading: false, initialized: true } : s
          )
        );
        return;
      }
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                conversationId: data.conversation_id,
                title: data.session_title ?? s.title,
                currentAgent: data.current_agent,
                context: data.context,
                events: (data.events || []).map((e: any) => ({
                  ...e,
                  timestamp: e.timestamp ?? Date.now(),
                })),
                agents: data.agents || [],
                guardrails: normalizeGuardrails(data.guardrails),
                messages: Array.isArray(data.messages)
                  ? data.messages.map((m: any) => ({
                      id: Date.now().toString() + Math.random().toString(),
                      content: m.content,
                      role: "assistant",
                      agent: m.agent,
                      traceId: data.trace_id,
                      timestamp: new Date(),
                    }))
                  : [],
                isLoading: false,
                initialized: true,
              }
            : s
        )
      );
    };

    bootSession(activeSessionId);
  }, [activeSessionId, sessions, userId]);

  // Send a user message
  const handleSendMessage = async (content: string) => {
    const session = sessions.find((s) => s.id === activeSessionId);
    if (!session) return;
    const status = session.context?.order_status ?? getOrderStatus(session.orderId);
    if (status === "canceled") {
      setOrderError("This session's order is canceled.");
      return;
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: new Date(),
    };

    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId
          ? { ...s, messages: [...s.messages, userMsg], isLoading: true }
          : s
      )
    );

    let data: any = null;
    try {
      data = await callChatAPI(
        content,
        session.conversationId ?? "",
        userId ?? undefined,
        session.orderId ?? undefined
      );
    } catch (err) {
      console.error("Failed to send message", err);
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId ? { ...s, isLoading: false } : s
        )
      );
      return;
    }

    if (!data) {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId ? { ...s, isLoading: false } : s
        )
      );
      return;
    }

    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== activeSessionId) return s;
        const stampedEvents = data.events
          ? data.events.map((e: any) => ({
              ...e,
              timestamp: e.timestamp ?? Date.now(),
            }))
          : [];
        const responses: Message[] = data.messages
          ? data.messages.map((m: any) => ({
              id: Date.now().toString() + Math.random().toString(),
              content: m.content,
              role: "assistant",
              agent: m.agent,
              traceId: data.trace_id,
              timestamp: new Date(),
            }))
          : [];
        return {
          ...s,
          conversationId: s.conversationId || data.conversation_id,
          title: data.session_title ?? s.title,
          currentAgent: data.current_agent,
          context: data.context,
          events: [...s.events, ...stampedEvents],
          agents: data.agents || s.agents,
          guardrails: normalizeGuardrails(data.guardrails) || s.guardrails,
          messages: [...s.messages, ...responses],
          isLoading: false,
        };
      })
    );
  };

  const handleFeedback = async (
    messageId: string,
    traceId: string,
    score: number
  ) => {
    setSessions((prev) =>
      prev.map((s) => ({
        ...s,
        messages: s.messages.map((m) =>
          m.id === messageId ? { ...m, rating: score } : m
        ),
      }))
    );
    if (!traceId) return;
    try {
      await submitFeedback(traceId, score);
    } catch (err) {
      console.error("Failed to submit feedback", err);
    }
  };

  const moveToFront = (sid: string) => {
    setSessions((prev) => {
      const target = prev.find((s) => s.id === sid);
      if (!target) return prev;
      const rest = prev.filter((s) => s.id !== sid);
      return [target, ...rest];
    });
  };

  const handleSelectSession = (sid: string) => {
    setActiveSessionId(sid);
    moveToFront(sid);
  };

  const handleCreateSession = () => {
    if (orders.length === 0) {
      setOrderError("No orders available. Create an order first.");
      return;
    }
    setIsOrderPickerOpen(true);
  };

  const handleCreateOrder = async () => {
    if (userId == null) return;
    try {
      await createOrder(userId);
      await loadOrders(userId);
    } catch (err) {
      console.error("Failed to create order", err);
      setOrderError("Failed to create order.");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("airloop_user");
    if (userId != null) {
      localStorage.removeItem(`airloop_sessions_v1_${userId}`);
    }
    setSessions([]);
    setActiveSessionId(null);
    setSessionCounter(0);
    setOrders([]);
    setUserId(null);
    setUserProfile(null);
    router.replace("/login");
  };

  const handleSelectOrderForSession = (order: Order) => {
    if (order.status === "canceled") {
      setOrderError("This order is canceled and cannot be used.");
      return;
    }
    const next = sessionCounter + 1;
    const newSession = createSession(`Order ${order.confirmation_number}`, order);
    setSessionCounter(next);
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setIsOrderPickerOpen(false);
  };

  if (!isAuthChecked) {
    return <main className="p-4 text-sm text-slate-500">Checking access...</main>;
  }

  return (
    <main className="h-screen overflow-hidden p-4 flex-shrink-0">
      <div
        className={`flex h-full flex-col lg:flex-row ${
          isAgentPanelCollapsed ? "gap-0" : "gap-4"
        }`}
      >
        <div
          className={`flex-shrink-0 overflow-hidden transition-[width,height,opacity] duration-300 ease-in-out lg:h-full ${
            isAgentPanelCollapsed
              ? "h-0 opacity-0 lg:w-0"
              : "h-[45%] opacity-100 lg:w-[42%]"
          }`}
        >
          <div className="h-full w-full lg:min-w-[320px]">
            <AgentPanel
              agents={activeSession?.agents || []}
              currentAgent={activeSession?.currentAgent || ""}
              events={activeSession?.events || []}
              guardrails={activeSession?.guardrails || []}
              context={activeSession?.context || {}}
              sessions={sessionOptions}
              orders={orders}
              ordersLoading={isOrdersLoading}
              ordersError={orderError}
              activeSessionId={activeSessionId}
              onSelectSession={handleSelectSession}
              onCreateSession={handleCreateSession}
              onCreateOrder={handleCreateOrder}
              onRefreshOrders={() => (userId != null ? loadOrders(userId) : null)}
            />
          </div>
        </div>
        <div
          className={`flex flex-1 flex-col overflow-hidden rounded-2xl border border-border-subtle bg-surface/85 shadow-panel backdrop-blur ${
            isAgentPanelCollapsed
              ? "h-full lg:mx-auto lg:max-w-[85%]"
              : "h-[55%] lg:h-full"
          }`}
        >
          <div className="flex min-h-[60px] items-center gap-3 border-b border-border-subtle/70 bg-surface-muted/80 px-4 py-3 backdrop-blur">
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-full border border-border-subtle bg-white/80 text-slate-600 shadow-soft transition-colors duration-200 hover:border-brand/40 hover:text-slate-900"
              onClick={() => setIsAgentPanelCollapsed((prev) => !prev)}
              aria-label={
                isAgentPanelCollapsed ? "Show agent control" : "Hide agent control"
              }
              aria-pressed={isAgentPanelCollapsed}
            >
              {isAgentPanelCollapsed ? (
                <Menu className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-slate-800">
                {activeSession?.title || "Session"}
              </div>
              {userProfile && (
                <div className="truncate text-xs text-slate-500">
                  {userProfile.username}
                  {userProfile.account_number ? ` · ${userProfile.account_number}` : ""}
                </div>
              )}
            </div>
            {activeSession?.conversationId && (
              <span className="hidden whitespace-nowrap rounded-full border border-border-subtle bg-white/80 px-3 py-1 text-xs font-medium text-slate-500 sm:inline-flex">
                ID: {activeSession.conversationId}
              </span>
            )}
            <button
              type="button"
              className="rounded-full border border-border-subtle px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors duration-200 hover:border-brand/40 hover:text-slate-900"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
          {activeSession ? (
            <Chat
              sessionId={activeSession?.id || ""}
              messages={activeSession?.messages || []}
              onSendMessage={handleSendMessage}
              onFeedback={handleFeedback}
              isLoading={activeSession?.isLoading}
            />
          ) : (
            <div className="flex flex-1 items-center justify-center px-6">
              <div className="max-w-sm rounded-2xl border border-border-subtle bg-white/80 p-6 text-center shadow-soft">
                <div className="text-sm font-semibold text-slate-800">
                  No active session
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Create a session by selecting one of your existing orders.
                </p>
                <button
                  type="button"
                  className="mt-4 rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white shadow-soft"
                  onClick={handleCreateSession}
                >
                  Create session
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      {isOrderPickerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/30 p-4">
          <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-white p-5 shadow-panel">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-800">
                Select an order
              </div>
              <button
                type="button"
                className="text-xs text-slate-500 hover:text-slate-700"
                onClick={() => setIsOrderPickerOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="mt-4 space-y-2">
              {orders.map((order) => (
                <button
                  key={order.id}
                  type="button"
                  className="w-full rounded-xl border border-border-subtle bg-white/90 px-3 py-2 text-left text-xs text-slate-700 transition-colors duration-150 hover:border-brand/40"
                  onClick={() => handleSelectOrderForSession(order)}
                >
                  <div className="font-semibold text-slate-800">
                    {order.confirmation_number}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-500">
                    Flight {order.flight_number} · Seat {order.seat_number}
                  </div>
                </button>
              ))}
              {orders.length === 0 && (
                <div className="text-xs text-slate-500">
                  No orders available. Create one first.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
