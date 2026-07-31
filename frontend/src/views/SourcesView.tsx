import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookMarked, ChevronDown, ChevronRight, ExternalLink, Plus, StickyNote, Trash2 } from "lucide-react";
import clsx from "clsx";
import { api, type NoteMeta, type Source } from "../api";

const STATUS: { key: Source["status"]; label: string; cls: string }[] = [
  { key: "to_read", label: "To read", cls: "text-amber-400 bg-amber-400/10" },
  { key: "reading", label: "Reading", cls: "text-sky-400 bg-sky-400/10" },
  { key: "read", label: "Read", cls: "text-emerald-400 bg-emerald-400/10" },
];

export default function SourcesView() {
  const [sources, setSources] = useState<Source[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", url: "", doi: "", authors: "", kind: "paper" });
  const [expanded, setExpanded] = useState<string | null>(null);
  const [linkedNotes, setLinkedNotes] = useState<Record<string, NoteMeta[]>>({});
  const navigate = useNavigate();

  const toggleExpand = async (id: string) => {
    if (expanded === id) {
      setExpanded(null);
      return;
    }
    setExpanded(id);
    if (!linkedNotes[id]) {
      const notes = await api.listNotes({ source_id: id });
      setLinkedNotes((prev) => ({ ...prev, [id]: notes }));
    }
  };

  const load = useCallback(async () => setSources(await api.listSources()), []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async () => {
    if (!form.title.trim()) return;
    await api.createSource({
      title: form.title.trim(),
      url: form.url.trim(),
      doi: form.doi.trim(),
      kind: form.kind,
      authors: form.authors.split(",").map((a) => a.trim()).filter(Boolean),
    });
    setForm({ title: "", url: "", doi: "", authors: "", kind: "paper" });
    setShowForm(false);
    void load();
  };

  const cycleStatus = async (s: Source) => {
    const order: Source["status"][] = ["to_read", "reading", "read"];
    const next = order[(order.indexOf(s.status) + 1) % order.length];
    await api.updateSource(s.id, { status: next });
    void load();
  };

  const remove = async (s: Source) => {
    await api.deleteSource(s.id);
    void load();
  };

  const input = "rounded-lg border border-ink-700 bg-ink-900 px-3 py-2 text-sm outline-none focus:border-accent-500 placeholder:text-ink-500 transition-colors";

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <header className="mb-5 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">Sources</h2>
          <p className="text-sm text-ink-300 mt-1">Papers, articles, and books — your reading list.</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-1.5 rounded-xl bg-accent-500 hover:bg-accent-400 text-white text-sm font-medium px-4 py-2 transition-colors"
        >
          <Plus size={15} /> Add source
        </button>
      </header>

      {showForm && (
        <div className="mb-6 rounded-xl border border-ink-800 bg-ink-900 p-4 grid grid-cols-2 gap-3">
          <input className={clsx(input, "col-span-2")} placeholder="Title *" value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <input className={input} placeholder="Authors (comma-separated)" value={form.authors}
            onChange={(e) => setForm({ ...form, authors: e.target.value })} />
          <select className={input} value={form.kind}
            onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            {["paper", "article", "book", "video", "other"].map((k) => (
              <option key={k} value={k}>{k}</option>
            ))}
          </select>
          <input className={input} placeholder="URL" value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })} />
          <input className={input} placeholder="DOI" value={form.doi}
            onChange={(e) => setForm({ ...form, doi: e.target.value })} />
          <div className="col-span-2 flex justify-end">
            <button onClick={() => void create()}
              className="rounded-lg bg-accent-500 hover:bg-accent-400 text-white text-sm font-medium px-4 py-2 transition-colors">
              Save
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {sources.length === 0 && (
          <div className="border border-dashed border-ink-700 rounded-xl py-16 text-center text-ink-500">
            <BookMarked className="mx-auto mb-3" size={28} />
            <p className="text-sm">No sources yet.</p>
          </div>
        )}
        {sources.map((s) => {
          const st = STATUS.find((x) => x.key === s.status)!;
          const isOpen = expanded === s.id;
          const notes = linkedNotes[s.id];
          return (
            <div key={s.id} className="group rounded-xl border border-ink-800 bg-ink-900">
              <div className="flex items-center gap-3 px-4 py-3">
                <button onClick={() => void toggleExpand(s.id)}
                  className="flex items-center gap-2 min-w-0 text-left">
                  {isOpen ? <ChevronDown size={14} className="shrink-0 text-ink-500" />
                          : <ChevronRight size={14} className="shrink-0 text-ink-500" />}
                  <span className="min-w-0">
                    <span className="block text-sm font-medium truncate">{s.title}</span>
                    <span className="block text-xs text-ink-500 truncate">
                      <span className="uppercase tracking-wide text-[10px] mr-2 text-ink-300">{s.kind}</span>
                      {s.authors.join(", ")}
                      {s.doi && <span className="ml-2 font-mono">{s.doi}</span>}
                    </span>
                  </span>
                </button>
                <div className="ml-auto flex items-center gap-2 shrink-0">
                  {s.url && (
                    <a href={s.url} target="_blank" rel="noreferrer"
                      className="text-ink-500 hover:text-accent-400 transition-colors">
                      <ExternalLink size={14} />
                    </a>
                  )}
                  <button onClick={() => void cycleStatus(s)}
                    className={clsx("rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors", st.cls)}>
                    {st.label}
                  </button>
                  <button onClick={() => void remove(s)}
                    className="opacity-0 group-hover:opacity-100 text-ink-500 hover:text-red-400 transition-all">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              {isOpen && (
                <div className="border-t border-ink-850 px-4 py-2.5">
                  <p className="text-[10px] uppercase tracking-wide text-ink-500 mb-1.5">
                    Notes from this source
                  </p>
                  {notes === undefined ? (
                    <p className="text-xs text-ink-500">Loading…</p>
                  ) : notes.length === 0 ? (
                    <p className="text-xs text-ink-500">
                      Nothing linked yet — open a note and use "Link source…".
                    </p>
                  ) : (
                    <div className="space-y-0.5">
                      {notes.map((n) => (
                        <button key={n.id} onClick={() => navigate(`/notes/${n.id}`)}
                          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-ink-100 hover:bg-ink-850 transition-colors">
                          <StickyNote size={13} className="shrink-0 text-accent-400" />
                          <span className="truncate">{n.title || "Untitled"}</span>
                          <span className="ml-auto shrink-0 text-[11px] text-ink-500">
                            {new Date(n.modified_at + "Z").toLocaleDateString()}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
