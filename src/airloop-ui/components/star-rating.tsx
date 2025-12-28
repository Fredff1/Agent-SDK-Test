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
          className="text-xs text-blue-700 hover:text-blue-800 bg-blue-50 px-2 py-1 rounded-full border border-blue-200 shadow-sm transition-all hover:shadow"
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
              <span className="text-2xl text-gray-300 select-none">★</span>
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
        className="px-3 py-1 rounded-full bg-gradient-to-r from-emerald-500 via-green-500 to-lime-400 text-white text-xs font-semibold shadow-sm hover:shadow-md transition-all disabled:opacity-60"
        disabled={selected === null || submitting}
        onClick={handleSubmit}
      >
        {submitting ? "Sending..." : "Submit"}
      </button>
          {toggleable && (
            <button
              type="button"
              className="text-xs text-gray-600 hover:text-gray-800 bg-gray-100 px-2 py-1 rounded-full border border-gray-200 transition-all"
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
