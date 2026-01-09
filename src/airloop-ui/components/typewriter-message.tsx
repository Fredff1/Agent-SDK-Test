"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";

interface TypewriterMessageProps {
  content: string;
  shouldAnimate: boolean;
  onStream?: () => void;
}

export function TypewriterMessage({
  content,
  shouldAnimate,
  onStream,
}: TypewriterMessageProps) {
  const tokens = useMemo(() => {
    const hasCjk = /[\u3040-\u30ff\u4e00-\u9fff]/.test(content);
    if (hasCjk) {
      return Array.from(content);
    }
    return content.split(/(\s+)/).filter((chunk) => chunk.length > 0);
  }, [content]);
  const [displayed, setDisplayed] = useState(shouldAnimate ? "" : content);

  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayed(content);
      return;
    }

    if (tokens.length === 0) {
      setDisplayed("");
      return;
    }

    let index = 0;
    setDisplayed("");

    let timeoutId: number | undefined;
    const baseDelay = 35;
    const sentencePause = 320;
    const clausePause = 140;

    const getDelay = (token: string) => {
      const trimmed = token.trim();
      if (/[.!?。！？]+$/.test(trimmed)) {
        return baseDelay + sentencePause;
      }
      if (/[，,;；、]+$/.test(trimmed)) {
        return baseDelay + clausePause;
      }
      return baseDelay;
    };

    const tick = () => {
      index = Math.min(index + 1, tokens.length);
      setDisplayed(tokens.slice(0, index).join(""));
      onStream?.();
      if (index >= tokens.length) {
        return;
      }
      timeoutId = window.setTimeout(tick, getDelay(tokens[index - 1] || ""));
    };

    timeoutId = window.setTimeout(tick, baseDelay);

    return () => {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [content, shouldAnimate, tokens, onStream]);

  return <ReactMarkdown>{displayed}</ReactMarkdown>;
}
