import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { Search, StickyNote, CheckSquare } from "lucide-react";
import clsx from "clsx";
import { api, type SearchHit } from "../api";

export default function CommandPalette({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => inputRef.current?.focus(), []);

  useEffect(() => {
    if (!query.trim()) {
      setHits([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const res = await api.search(query);
        setHits(res.hits);
        setSelected(0);
      } catch {
        setHits([]);
      }
    }, 120);
    return () => clearTimeout(t);
  }, [query]);

  const open = (hit: SearchHit) => {
    onClose();
    navigate(hit.entity_type === "note" ? `/notes/${hit.entity_id}` : "/tasks");
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-start justify-center pt-[14vh]"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-[640px] max-w-[92vw] rounded-xl border border-ink-700 bg-ink-900 shadow-2xl overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-ink-800">
          <Search size={17} className="text-ink-500" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setSelected((s) => Math.min(s + 1, hits.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setSelected((s) => Math.max(s - 1, 0));
              } else if (e.key === "Enter" && hits[selected]) {
                open(hits[selected]);
              }
            }}
            placeholder="Search notes and tasks…"
            className="flex-1 bg-transparent outline-none text-[15px] placeholder:text-ink-500"
          />
        </div>
        <div className="max-h-[50vh] overflow-y-auto">
          {hits.length === 0 && query.trim() && (
            <div className="px-4 py-6 text-sm text-ink-500">No results</div>
          )}
          {hits.map((hit, i) => (
            <button
              key={`${hit.entity_type}-${hit.entity_id}`}
              onClick={() => open(hit)}
              onMouseEnter={() => setSelected(i)}
              className={clsx(
                "w-full text-left px-4 py-2.5 flex gap-3 items-start",
                i === selected ? "bg-ink-800" : "",
              )}
            >
              {hit.entity_type === "note" ? (
                <StickyNote size={15} className="mt-0.5 shrink-0 text-accent-400" />
              ) : (
                <CheckSquare size={15} className="mt-0.5 shrink-0 text-emerald-400" />
              )}
              <span className="min-w-0">
                <span className="block text-sm text-ink-100 truncate">{hit.title || "Untitled"}</span>
                <span
                  className="block text-xs text-ink-300 truncate"
                  dangerouslySetInnerHTML={{ __html: hit.snippet }}
                />
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
