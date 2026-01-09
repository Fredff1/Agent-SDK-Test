import { useState } from "react";

interface StarRatingProps {
  traceId: string;
  onFeedback?: (traceId: string, score: number) => void;
  showToggle?: boolean;
  onClose?: () => void;
}

export function StarRating({ traceId, onFeedback, showToggle = true, onClose }: StarRatingProps) {
  const toggleable = showToggle !== false;
  const [open, setOpen] = useState(!toggleable);
  const [selected, setSelected] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!traceId || selected === null) return;
    try {
      setSubmitting(true);
      await onFeedback?.(traceId, selected);
      if (toggleable) {
        setOpen(false);
      }
      onClose?.();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-2">
      {toggleable && !open ? (
        <button
          type="button"
          className="rounded-full border border-brand/30 bg-brand/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-brand transition-colors hover:bg-brand/20"
          onClick={() => setOpen(true)}
        >
          Rate
        </button>
      ) : (
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => {
          const fillPercent = Math.max(
            0,
            Math.min(1, (selected ?? 0) - (star - 1))
          );
          return (
            <div key={star} className="relative">
              <span className="text-2xl text-slate-300 select-none">★</span>
              <span
                className="absolute inset-0 overflow-hidden text-2xl text-amber-500 select-none pointer-events-none"
                style={{ width: `${fillPercent * 100}%` }}
              >
                ★
              </span>
              <div className="absolute inset-0 flex">
                <button
                  type="button"
                  className="h-full w-1/2"
                  onClick={() => setSelected(star - 0.5)}
                  aria-label={`Rate ${star - 0.5} stars`}
                />
                <button
                  type="button"
                  className="h-full w-1/2"
                  onClick={() => setSelected(star)}
                  aria-label={`Rate ${star} stars`}
                />
              </div>
            </div>
          );
        })}
      </div>
      <button
        type="button"
        className="rounded-full bg-brand px-3 py-1 text-xs font-semibold text-brand-foreground shadow-soft transition-colors hover:opacity-90 disabled:opacity-60"
        disabled={selected === null || submitting}
        onClick={handleSubmit}
      >
        {submitting ? "Sending..." : "Submit"}
      </button>
          {toggleable && (
            <button
              type="button"
              className="rounded-full border border-border-subtle bg-slate-100 px-2 py-1 text-xs text-slate-600 transition-colors hover:text-slate-800"
              onClick={() => {
                setOpen(false);
                onClose?.();
              }}
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </div>
  );
}
