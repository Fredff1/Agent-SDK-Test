"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import type { Message } from "@/lib/types";
import { SeatMap } from "./seat-map";
import { StarRating } from "./star-rating";
import { TypewriterMessage } from "./typewriter-message";

interface ChatProps {
  sessionId: string;
  messages: Message[];
  onSendMessage: (message: string) => void;
  /** Whether waiting for assistant response */
  isLoading?: boolean;
  onFeedback?: (messageId: string, traceId: string, score: number) => void;
}

export function Chat({
  sessionId,
  messages,
  onSendMessage,
  isLoading,
  onFeedback,
}: ChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [inputText, setInputText] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const [showSeatMap, setShowSeatMap] = useState(false);
  const [selectedSeat, setSelectedSeat] = useState<string | undefined>(undefined);
  const [ratingOpenId, setRatingOpenId] = useState<string | null>(null);
  const animatedMessageIdsRef = useRef<Set<string>>(new Set());
  const lastSessionIdRef = useRef<string | null>(null);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  // Auto-scroll to bottom when messages or loading indicator change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
  }, [messages, isLoading]);

  // Watch for special seat map trigger message (anywhere in list) and only if a seat has not been picked yet
  useEffect(() => {
    const hasTrigger = messages.some(
      (m) => m.role === "assistant" && m.content === "DISPLAY_SEAT_MAP"
    );
    // Show map if trigger exists and seat not chosen yet
    if (hasTrigger && !selectedSeat) {
      setShowSeatMap(true);
    }
  }, [messages, selectedSeat]);

  useEffect(() => {
    if (lastSessionIdRef.current === sessionId) return;
    lastSessionIdRef.current = sessionId;
    animatedMessageIdsRef.current = new Set(messages.map((message) => message.id));
    setStreamingMessageId(null);
  }, [messages, sessionId]);

  useEffect(() => {
    const newAssistantMessages = messages.filter(
      (message) =>
        message.role === "assistant" &&
        message.content !== "DISPLAY_SEAT_MAP" &&
        !animatedMessageIdsRef.current.has(message.id)
    );
    if (newAssistantMessages.length === 0) return;

    newAssistantMessages.forEach((message) =>
      animatedMessageIdsRef.current.add(message.id)
    );
    const latest = newAssistantMessages[newAssistantMessages.length - 1];
    setStreamingMessageId((prev) => (prev === latest.id ? prev : latest.id));
  }, [messages]);

  const handleStreamTick = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
  }, []);

  const formatRatingValue = useCallback((score: number) => {
    return Number.isInteger(score) ? `${score}` : score.toFixed(1);
  }, []);

  const handleSend = useCallback(() => {
    if (!inputText.trim()) return;
    onSendMessage(inputText);
    setInputText("");
  }, [inputText, onSendMessage]);

  const handleSeatSelect = useCallback(
    (seat: string) => {
      setSelectedSeat(seat);
      setShowSeatMap(false);
      onSendMessage(`I would like seat ${seat}`);
    },
    [onSendMessage]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !isComposing) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend, isComposing]
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto px-5 pb-8 pt-4">
        {messages.map((msg) => {
          if (msg.content === "DISPLAY_SEAT_MAP") return null; // Skip rendering marker message
          const shouldStream =
            msg.role === "assistant" && msg.id === streamingMessageId;
          const rating = msg.rating;
          const ratingLabel =
            rating !== undefined
              ? `user rate: ${formatRatingValue(rating)}`
              : "Rate response";
          return (
            <div
              key={msg.id}
              className={`mb-6 flex animate-in fade-in slide-in-from-bottom-2 duration-200 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div className="flex max-w-[78%] flex-col gap-2">
                <div
                  className={`rounded-2xl px-4 py-2 text-sm leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "rounded-br-md bg-slate-900 text-slate-50 md:ml-12"
                      : "rounded-bl-md border border-border-subtle bg-white/80 text-slate-800 md:mr-12"
                  }`}
                >
                  <TypewriterMessage
                    content={msg.content}
                    shouldAnimate={shouldStream}
                    onStream={shouldStream ? handleStreamTick : undefined}
                  />
                </div>
                {msg.role === "assistant" && msg.traceId && (
                  <>
                    <button
                      type="button"
                      className="self-start rounded-full border border-brand/30 bg-brand/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-brand transition-colors duration-200 hover:bg-brand/20"
                      onClick={() =>
                        setRatingOpenId((prev) => (prev === msg.id ? null : msg.id))
                      }
                    >
                      {ratingLabel}
                    </button>
                    {ratingOpenId === msg.id && (
                      <div className="self-start rounded-xl border border-border-subtle bg-white/90 px-4 py-3 shadow-soft">
                        <StarRating
                          traceId={msg.traceId}
                          onFeedback={(traceId, score) =>
                            onFeedback?.(msg.id, traceId, score)
                          }
                          showToggle={false}
                          onClose={() => setRatingOpenId(null)}
                        />
                        <button
                          type="button"
                          className="mt-2 text-xs text-slate-500 underline hover:text-slate-700"
                          onClick={() => setRatingOpenId(null)}
                        >
                          Close
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
        {showSeatMap && (
          <div className="mb-5 flex justify-start">
            <div className="mr-4 rounded-2xl md:mr-24">
              <SeatMap
                onSeatSelect={handleSeatSelect}
                selectedSeat={selectedSeat}
              />
            </div>
          </div>
        )}
        {isLoading && (
          <div className="mb-5 flex items-center gap-2 text-sm">
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
            <span
              className="h-2 w-2 animate-pulse rounded-full bg-slate-400"
              style={{ animationDelay: "0.15s" }}
            />
            <span
              className="h-2 w-2 animate-pulse rounded-full bg-slate-400"
              style={{ animationDelay: "0.3s" }}
            />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-border-subtle bg-surface-muted/80 px-4 py-3">
        <div className="flex items-end gap-3 rounded-2xl border border-border-subtle bg-white/90 p-3 shadow-soft transition-colors duration-200 focus-within:border-brand/40 focus-within:ring-2 focus-within:ring-brand/10">
          <textarea
            id="prompt-textarea"
            tabIndex={0}
            dir="auto"
            rows={2}
            placeholder="Send a request..."
            className="min-h-[44px] flex-1 resize-none bg-transparent text-sm leading-relaxed text-slate-800 placeholder:text-slate-400 focus:outline-none"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
          />
          <button
            disabled={!inputText.trim()}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-brand text-brand-foreground shadow-soft transition-colors duration-200 hover:opacity-90 disabled:bg-slate-200 disabled:text-slate-400"
            onClick={handleSend}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                fill="currentColor"
                fillRule="evenodd"
                d="M11.34 3.44a.9.9 0 0 1 1.32 0l7.02 7.12a.9.9 0 0 1-1.3 1.24l-5.47-5.56v13.82a.9.9 0 1 1-1.8 0V6.24L5.64 11.8a.9.9 0 0 1-1.3-1.24l7.02-7.12Z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
