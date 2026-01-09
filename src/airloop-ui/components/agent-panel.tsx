"use client";

import { Bot } from "lucide-react";
import type { Agent, AgentEvent, GuardrailCheck } from "@/lib/types";
import { AgentsList } from "./agents-list";
import { Guardrails } from "./guardrails";
import { ConversationContext } from "./conversation-context";
import { RunnerOutput } from "./runner-output";
import { SessionSwitcher, type SessionOption } from "./session-switcher";

interface AgentPanelProps {
  agents: Agent[];
  currentAgent: string;
  events: AgentEvent[];
  guardrails: GuardrailCheck[];
  sessions: SessionOption[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateSession: () => void;
  context: {
    passenger_name?: string;
    confirmation_number?: string;
    seat_number?: string;
    flight_number?: string;
    account_number?: string;
  };
}

export function AgentPanel({
  agents,
  currentAgent,
  events,
  guardrails,
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  context,
}: AgentPanelProps) {
  const activeAgent = agents.find((a) => a.name === currentAgent);
  const runnerEvents = events.filter((e) => e.type !== "message");

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-border-subtle bg-surface/85 shadow-panel backdrop-blur">
      <div className="flex min-h-[60px] items-center justify-between border-b border-border-subtle/70 bg-surface-muted/80 px-5 py-3">
        <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-600">
          <Bot className="h-4 w-4 text-brand" />
          Agent Control
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
          Ops Console
        </span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-5">
        <SessionSwitcher
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={onSelectSession}
          onCreate={onCreateSession}
        />
        <AgentsList agents={agents} currentAgent={currentAgent} />
        <Guardrails
          guardrails={guardrails}
          inputGuardrails={activeAgent?.input_guardrails ?? []}
        />
        <ConversationContext context={context} />
        <RunnerOutput runnerEvents={runnerEvents} />
      </div>
    </div>
  );
}
