import { useEffect, useRef, useState } from "react";
import { Zap } from "lucide-react";
import { api } from "../api";

// Views listen for this so fresh captures appear without a manual refresh.
export const CAPTURE_EVENT = "pra-captured";

export default function QuickCapture({ onClose }: { onClose: () => void }) {
  const [text, setText] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => ref.current?.focus(), []);

  const submit = async () => {
    if (!text.trim()) return;
    setError(null);
    try {
      const result = await api.capture(text, sourceUrl.trim());
      window.dispatchEvent(new Event(CAPTURE_EVENT));
      setStatus(result.kind === "task" ? "Task created ✓" : "Saved to inbox ✓");
      setText("");
      setSourceUrl("");
      setTimeout(() => setStatus(null), 1500);
      ref.current?.focus();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-start justify-center pt-[18vh]"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-[600px] max-w-[92vw] rounded-xl border border-ink-700 bg-ink-900 shadow-2xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 pt-3 text-ink-300 text-xs">
          <Zap size={14} className="text-accent-400" />
          Quick capture — plain text saves a snippet, <code className="font-mono bg-ink-800 rounded px-1">todo:</code> creates a task
          {status && <span className="ml-auto text-emerald-400">{status}</span>}
          {error && <span className="ml-auto text-red-400">{error}</span>}
        </div>
        <textarea
          ref={ref}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              void submit();
            }
          }}
          rows={5}
          placeholder={"Paste a snippet…\nor: todo: review paper draft friday 2pm #thesis p1"}
          className="w-full bg-transparent px-4 py-3 text-[15px] outline-none resize-none placeholder:text-ink-500 font-mono"
        />
        <div className="flex items-center gap-2 border-t border-ink-800 px-4 py-2.5">
          <input
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            placeholder="Source URL (optional)"
            className="flex-1 bg-ink-850 rounded-md px-3 py-1.5 text-xs outline-none placeholder:text-ink-500"
          />
          <button
            onClick={() => void submit()}
            className="rounded-md bg-accent-500 hover:bg-accent-400 text-white text-xs font-medium px-4 py-1.5 transition-colors"
          >
            Save <kbd className="font-mono opacity-70 ml-1">Ctrl ⏎</kbd>
          </button>
        </div>
      </div>
    </div>
  );
}
