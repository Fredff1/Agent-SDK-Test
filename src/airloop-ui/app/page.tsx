"use client";

import { useEffect, useState } from "react";
import { AgentPanel } from "@/components/agent-panel";
import { Chat } from "@/components/Chat";
import type { Agent, AgentEvent, GuardrailCheck, Message } from "@/lib/types";
import { callChatAPI, submitFeedback } from "@/lib/api";

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

  // Load sessions from localStorage on first mount
  useEffect(() => {
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

  const handleFeedback = async (traceId: string, score: number) => {
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

  if (!activeSession) {
    return <main className="p-4 text-sm text-gray-500">Loading sessions...</main>;
  }

  return (
    <main className="flex h-screen gap-2 bg-gray-100 p-2">
      <AgentPanel
        agents={activeSession?.agents || []}
        currentAgent={activeSession?.currentAgent || ""}
        events={activeSession?.events || []}
        guardrails={activeSession?.guardrails || []}
        context={activeSession?.context || {}}
      />
      <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="flex items-center gap-2 p-3 border-b border-gray-200 bg-gray-50">
          <div className="flex flex-wrap gap-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  s.id === activeSessionId
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
                onClick={() => {
                  setActiveSessionId(s.id);
                  moveToFront(s.id);
                }}
              >
                {s.title}
              </button>
            ))}
          </div>
          <button
            className="ml-auto px-3 py-1 rounded-full text-sm border border-dashed border-gray-400 text-gray-700 hover:border-blue-400 hover:text-blue-600 transition-colors"
            onClick={() => {
              const next = sessionCounter + 1;
              const newSession = createSession(`Session ${next}`);
              setSessionCounter(next);
              setSessions((prev) => [newSession, ...prev]);
              setActiveSessionId(newSession.id);
            }}
          >
            + New
          </button>
        </div>
        <Chat
          messages={activeSession?.messages || []}
          onSendMessage={handleSendMessage}
          onFeedback={handleFeedback}
          isLoading={activeSession?.isLoading}
        />
      </div>
    </main>
  );
}
