"use client";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AgentEvent } from "@/lib/types";
import {
  ArrowRightLeft,
  Wrench,
  WrenchIcon,
  RefreshCw,
  MessageSquareMore,
} from "lucide-react";
import { PanelSection } from "./panel-section";

interface RunnerOutputProps {
  runnerEvents: AgentEvent[];
}

function formatEventName(type: string) {
  return (type.charAt(0).toUpperCase() + type.slice(1)).replace("_", " ");
}

function EventIcon({ type }: { type: string }) {
  const className = "h-4 w-4 text-slate-500";
  switch (type) {
    case "handoff":
      return <ArrowRightLeft className={className} />;
    case "tool_call":
      return <Wrench className={className} />;
    case "tool_output":
      return <WrenchIcon className={className} />;
    case "context_update":
      return <RefreshCw className={className} />;
    default:
      return null;
  }
}

function EventDetails({ event }: { event: AgentEvent }) {
  let details = null;
  const className =
    "rounded-md border border-border-subtle/70 bg-slate-50/70 p-2.5 text-xs text-slate-600";
  switch (event.type) {
    case "handoff":
      details = event.metadata && (
        <div className={className}>
          <div className="text-slate-600">
            <span className="font-medium text-slate-600">From:</span>{" "}
            {event.metadata.source_agent}
          </div>
          <div className="text-slate-600">
            <span className="font-medium text-slate-600">To:</span>{" "}
            {event.metadata.target_agent}
          </div>
        </div>
      );
      break;
    case "tool_call":
      details = event.metadata && event.metadata.tool_args && (
        <div className={className}>
          <div className="mb-1 text-xs font-medium text-slate-600">
            Arguments
          </div>
          <pre className="overflow-x-auto rounded bg-slate-50/70 p-2 text-xs text-slate-600">
            {JSON.stringify(event.metadata.tool_args, null, 2)}
          </pre>
        </div>
      );
      break;
    case "tool_output":
      details = event.metadata && event.metadata.tool_result && (
        <div className={className}>
          <div className="mb-1 text-xs font-medium text-slate-600">Result</div>
          <pre className="overflow-x-auto rounded bg-slate-50/70 p-2 text-xs text-slate-600">
            {JSON.stringify(event.metadata.tool_result, null, 2)}
          </pre>
        </div>
      );
      break;
    case "context_update":
      details = event.metadata?.changes && (
        <div className={className}>
          {Object.entries(event.metadata.changes).map(([key, value]) => (
            <div key={key} className="text-xs">
              <div className="text-slate-600">
                <span className="font-medium text-slate-600">{key}:</span>{" "}
                {value ?? "null"}
              </div>
            </div>
          ))}
        </div>
      );
      break;
    default:
      return null;
  }

  return (
    <div className="mt-1 text-sm">
      {event.content && (
        <div className="mb-2 font-mono text-slate-700">{event.content}</div>
      )}
      {details}
    </div>
  );
}

function TimeBadge({ timestamp }: { timestamp: Date }) {
  const date =
    timestamp && typeof (timestamp as any)?.toDate === "function"
      ? (timestamp as any).toDate()
      : timestamp;
  const formattedDate = new Date(date).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  return (
    <Badge
      variant="outline"
      className="h-5 bg-white/80 text-[10px] text-slate-500 border-border-subtle"
    >
      {formattedDate}
    </Badge>
  );
}

export function RunnerOutput({ runnerEvents }: RunnerOutputProps) {
  return (
    <div className="flex-1 overflow-hidden">
      <PanelSection title="Runner Output" icon={<MessageSquareMore className="h-4 w-4 text-brand" />}>
        <ScrollArea className="h-[calc(100%-2rem)] rounded-xl border border-border-subtle bg-surface-muted/70">
        <div className="space-y-3 p-4">
          {runnerEvents.length === 0 ? (
            <p className="p-4 text-center text-slate-500">
              No runner events yet
            </p>
          ) : (
            runnerEvents.map((event) => (
              <Card
                key={event.id}
                className="rounded-xl border border-border-subtle bg-white/85 shadow-soft"
              >
                <CardHeader className="flex flex-row justify-between items-center p-4">
                  <span className="text-sm font-semibold text-slate-800">
                    {event.agent}
                  </span>
                  <TimeBadge timestamp={event.timestamp} />
                </CardHeader>

                <CardContent className="flex items-start gap-3 p-4">
                  <div className="flex items-center gap-2 rounded-full bg-slate-100/80 p-2">
                    <EventIcon type={event.type} />
                    <div className="text-xs text-slate-600">
                      {formatEventName(event.type)}
                    </div>
                  </div>

                  <div className="flex-1">
                    <EventDetails event={event} />
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
        </ScrollArea>
      </PanelSection>
    </div>
  );
}
