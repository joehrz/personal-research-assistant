import { useRef, useState } from "react";
import { Zap } from "lucide-react";
import { api } from "../api";

/**
 * Full-screen capture page for phones — the PWA's start screen.
 * Reachable at #/capture; posts into the same inbox as everything else.
 */
export default function MobileCaptureView() {
  const [text, setText] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const ref = useRef<HTMLTextAreaElement>(null);

  const save = async () => {
    if (!text.trim()) return;
    try {
      const result = await api.capture(text, sourceUrl.trim());
      setStatus({ ok: true, msg: result.kind === "task" ? "Task created ✓" : "Saved to inbox ✓" });
      setText("");
      setSourceUrl("");
      ref.current?.focus();
      setTimeout(() => setStatus(null), 2000);
    } catch (e) {
      setStatus({ ok: false, msg: `Failed: ${(e as Error).message}` });
    }
  };

  return (
    <div className="flex h-full flex-col bg-ink-950 p-4 gap-3">
      <header className="flex items-center gap-2">
        <Zap size={18} className="text-accent-400" />
        <h1 className="text-sm font-bold">
          Research<span className="text-accent-400"> Assistant</span> — capture
        </h1>
        {status && (
          <span className={`ml-auto text-xs ${status.ok ? "text-emerald-400" : "text-red-400"}`}>
            {status.msg}
          </span>
        )}
      </header>
      <textarea
        ref={ref}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={"Capture a thought…\nor: todo: email advisor tomorrow p1"}
        className="flex-1 w-full resize-none rounded-xl border border-ink-700 bg-ink-900 p-4 text-[16px] outline-none focus:border-accent-500 placeholder:text-ink-500"
        autoFocus
      />
      <input
        value={sourceUrl}
        onChange={(e) => setSourceUrl(e.target.value)}
        placeholder="Source URL (optional)"
        className="w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3 text-sm outline-none focus:border-accent-500 placeholder:text-ink-500"
      />
      <div className="flex gap-2">
        <a
          href="#/"
          className="rounded-xl bg-ink-800 px-4 py-3.5 text-sm text-ink-300 hover:text-ink-100 transition-colors"
        >
          Open app
        </a>
        <button
          onClick={() => void save()}
          className="flex-1 rounded-xl bg-accent-500 hover:bg-accent-400 py-3.5 text-sm font-semibold text-white transition-colors"
        >
          Save to inbox
        </button>
      </div>
    </div>
  );
}
