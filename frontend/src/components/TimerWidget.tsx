import { useCallback, useEffect, useState } from "react";
import { Play, Square, Timer } from "lucide-react";
import { api, type TimeEntry } from "../api";

// Other views dispatch this after starting/stopping a timer so the sidebar
// widget refreshes immediately instead of waiting for the next poll.
export const TIMER_EVENT = "pra-timer-changed";
export const notifyTimerChanged = () => window.dispatchEvent(new Event(TIMER_EVENT));

function elapsedLabel(startedAtIso: string): string {
  // time entries are stored as local wall-clock time (no timezone suffix)
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(startedAtIso).getTime()) / 1000));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
    : `${m}:${String(s).padStart(2, "0")}`;
}

export default function TimerWidget() {
  const [entry, setEntry] = useState<TimeEntry | null>(null);
  const [, setTick] = useState(0);

  const refresh = useCallback(() => {
    api.currentTimer().then(setEntry).catch(() => setEntry(null));
  }, []);

  useEffect(() => {
    refresh();
    const poll = setInterval(refresh, 30_000);
    const tick = setInterval(() => setTick((t) => t + 1), 1000);
    window.addEventListener(TIMER_EVENT, refresh);
    return () => {
      clearInterval(poll);
      clearInterval(tick);
      window.removeEventListener(TIMER_EVENT, refresh);
    };
  }, [refresh]);

  const start = async () => {
    setEntry(await api.startTimer({ label: "Focus" }));
  };
  const stop = async () => {
    await api.stopTimer();
    setEntry(null);
  };

  if (entry) {
    return (
      <div className="mx-3 mb-2 rounded-lg border border-accent-500/40 bg-accent-500/10 px-3 py-2">
        <div className="flex items-center gap-2">
          <Timer size={14} className="text-accent-400 shrink-0" />
          <span className="min-w-0 truncate text-xs text-ink-100">{entry.label}</span>
          <button
            onClick={() => void stop()}
            title="Stop timer"
            className="ml-auto shrink-0 rounded-md p-1 text-ink-300 hover:bg-ink-800 hover:text-red-400 transition-colors"
          >
            <Square size={12} />
          </button>
        </div>
        <p className="mt-0.5 font-mono text-lg font-semibold text-accent-400 tabular-nums">
          {elapsedLabel(entry.started_at)}
        </p>
      </div>
    );
  }

  return (
    <button
      onClick={() => void start()}
      className="mx-3 mb-2 flex items-center gap-2 rounded-lg bg-ink-800 hover:bg-ink-700 px-3 py-2 text-xs text-ink-300 hover:text-ink-100 transition-colors"
    >
      <Play size={13} /> Start focus timer
    </button>
  );
}
