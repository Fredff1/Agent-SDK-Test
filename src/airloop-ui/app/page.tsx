"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, Menu } from "lucide-react";
import { AgentPanel } from "@/components/agent-panel";
import { Chat } from "@/components/Chat";
import type { Agent, AgentEvent, GuardrailCheck, Message } from "@/lib/types";
import { callChatAPI, submitFeedback, fetchSessions } from "@/lib/api";

type Session = {
  id: string;
  title: string;
  conversationId: string | null;
  messages: Message[];
  events: AgentEvent[];
  agents: Agent[];
  currentAgent: string;
  guardrails: GuardrailCheck[];
  context: Record<string, any>;
  isLoading: boolean;
  initialized: boolean;
};

const createSession = (title: string): Session => ({
  id: Math.random().toString(36).slice(2),
  title,
  conversationId: null,
  messages: [],
  events: [],
  agents: [],
  currentAgent: "",
  guardrails: [],
  context: {},
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
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionCounter, setSessionCounter] = useState(1);
  const [isAgentPanelCollapsed, setIsAgentPanelCollapsed] = useState(false);

  // Load sessions from API (persistent store) first; fallback to localStorage
  useEffect(() => {
    (async () => {
      try {
        const apiSessions = await fetchSessions(50);
        if (Array.isArray(apiSessions) && apiSessions.length > 0) {
          const restored: Session[] = apiSessions.map((s: any, idx: number) => ({
            id: s.conversation_id || `session-${idx}`,
            title: s.conversation_id || `Session ${idx + 1}`,
            conversationId: s.conversation_id || null,
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
            context: s.context || {},
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
        const raw = localStorage.getItem("airloop_sessions_v1");
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
      const first = createSession("Session 1");
      setSessions([first]);
      setActiveSessionId(first.id);
      setSessionCounter(1);
    })();
  }, []);

  // Persist sessions to localStorage
  useEffect(() => {
    if (sessions.length === 0) return;
    try {
      localStorage.setItem(
        "airloop_sessions_v1",
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

    const bootSession = async (sessionId: string) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId ? { ...s, isLoading: true } : s
      )
    );
      let data: any = null;
      try {
        data = await callChatAPI("", "");
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
  }, [activeSessionId, sessions]);

  // Send a user message
  const handleSendMessage = async (content: string) => {
    const session = sessions.find((s) => s.id === activeSessionId);
    if (!session) return;

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
      data = await callChatAPI(content, session.conversationId ?? "");
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
    const next = sessionCounter + 1;
    const newSession = createSession(`Session ${next}`);
    setSessionCounter(next);
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  if (!activeSession) {
    return <main className="p-4 text-sm text-slate-500">Loading sessions...</main>;
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
              activeSessionId={activeSessionId}
              onSelectSession={handleSelectSession}
              onCreateSession={handleCreateSession}
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
            </div>
            {activeSession?.conversationId && (
              <span className="hidden whitespace-nowrap rounded-full border border-border-subtle bg-white/80 px-3 py-1 text-xs font-medium text-slate-500 sm:inline-flex">
                ID: {activeSession.conversationId}
              </span>
            )}
          </div>
          <Chat
            sessionId={activeSession?.id || ""}
            messages={activeSession?.messages || []}
            onSendMessage={handleSendMessage}
            onFeedback={handleFeedback}
            isLoading={activeSession?.isLoading}
          />
        </div>
      </div>
    </main>
  );
}
