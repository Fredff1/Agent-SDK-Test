"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, MessageSquare } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

export type SessionOption = {
  id: string;
  title: string;
  subtitle?: string;
};

interface SessionSwitcherProps {
  sessions: SessionOption[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
}

export function SessionSwitcher({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
}: SessionSwitcherProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const activeSession =
    sessions.find((session) => session.id === activeSessionId) ?? sessions[0];

  useEffect(() => {
    if (!open) return;

    const handleClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);

    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="mb-4">
      <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-600">
        <div className="flex items-center gap-2">
          <span className="rounded-md bg-brand/10 p-1.5 text-brand shadow-sm">
            <MessageSquare className="h-4 w-4" />
          </span>
          Session Switcher
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center justify-between rounded-xl border border-border-subtle bg-white/80 px-3 py-2 text-left text-sm text-slate-800 shadow-soft transition-colors duration-200 hover:border-brand/30"
          onClick={() => setOpen((prev) => !prev)}
          aria-haspopup="listbox"
          aria-expanded={open}
        >
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">
              {activeSession?.title || "No sessions"}
            </div>
            <div className="truncate text-xs text-slate-500">
              {activeSession?.subtitle || "No messages yet"}
            </div>
          </div>
          <ChevronDown
            className={`h-4 w-4 text-slate-500 transition-transform duration-200 ${
              open ? "rotate-180" : ""
            }`}
          />
        </button>
        <button
          type="button"
          className="whitespace-nowrap rounded-full border border-dashed border-border-subtle px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors duration-200 hover:border-brand/50 hover:text-slate-900"
          onClick={onCreate}
        >
          + New
        </button>
      </div>
      {open && (
        <div className="relative mt-2 rounded-xl border border-border-subtle bg-white/95 shadow-panel backdrop-blur">
          <ScrollArea className="max-h-64">
            <div className="p-1" role="listbox">
              {sessions.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-500">
                  No sessions available
                </div>
              ) : (
                sessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    role="option"
                    aria-selected={session.id === activeSessionId}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors duration-150 ${
                      session.id === activeSessionId
                        ? "bg-brand/10 text-slate-900"
                        : "text-slate-700 hover:bg-slate-100"
                    }`}
                    onClick={() => {
                      onSelect(session.id);
                      setOpen(false);
                    }}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-semibold">
                        {session.title}
                      </div>
                      <div className="truncate text-xs text-slate-500">
                        {session.subtitle || "No messages yet"}
                      </div>
                    </div>
                    {session.id === activeSessionId && (
                      <Check className="h-4 w-4 text-brand" />
                    )}
                  </button>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
