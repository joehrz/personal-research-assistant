import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { BookMarked, Eye, Link2, Pencil, Plus, Trash2, ExternalLink, X } from "lucide-react";
import clsx from "clsx";
import { api, type Note, type NoteMeta, type Source } from "../api";

// Turn [[Target]] / [[Target|label]] into markdown links to resolved notes;
// unresolved targets render as plain text with the brackets kept visible.
function renderWikilinks(content: string, links: Note["links"]): string {
  const byTitle = new Map(links.map((l) => [l.title.toLowerCase(), l.id]));
  return content.replace(
    /\[\[([^\[\]|\n]+?)(?:\|([^\[\]\n]+?))?\]\]/g,
    (whole, target: string, label?: string) => {
      const id = byTitle.get(target.trim().toLowerCase());
      return id ? `[${(label ?? target).trim()}](#/notes/${id})` : whole;
    },
  );
}

export default function NotesView() {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const [notes, setNotes] = useState<NoteMeta[]>([]);
  const [active, setActive] = useState<Note | null>(null);
  const [draft, setDraft] = useState("");
  const [title, setTitle] = useState("");
  const [preview, setPreview] = useState(false);
  const [saved, setSaved] = useState(true);
  const [backlinks, setBacklinks] = useState<NoteMeta[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [wiki, setWiki] = useState<{ query: string; start: number; index: number } | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const wikiMatches = useMemo(() => {
    if (wiki === null) return [];
    const q = wiki.query.toLowerCase();
    return notes
      .filter((n) => n.id !== active?.id && n.title.toLowerCase().includes(q))
      .slice(0, 6);
  }, [wiki, notes, active]);

  const previewText = useMemo(
    () => (active ? renderWikilinks(draft, active.links) : draft),
    [draft, active],
  );

  const loadList = useCallback(async () => {
    setNotes(await api.listNotes({ inbox: false }));
  }, []);

  useEffect(() => {
    void loadList();
    api.listSources().then(setSources).catch(() => setSources([]));
  }, [loadList]);

  useEffect(() => {
    if (!noteId) {
      setActive(null);
      return;
    }
    api.getNote(noteId).then((n) => {
      setActive(n);
      setDraft(n.content);
      setTitle(n.title);
      setSaved(true);
    }).catch(() => navigate("/notes"));
    api.getBacklinks(noteId).then(setBacklinks).catch(() => setBacklinks([]));
  }, [noteId, navigate]);

  // Debounced autosave.
  const scheduleSave = (nextTitle: string, nextContent: string) => {
    setSaved(false);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      if (!active) return;
      const updated = await api.updateNote(active.id, { title: nextTitle, content: nextContent });
      setActive((prev) => (prev && prev.id === updated.id ? { ...prev, links: updated.links } : prev));
      setSaved(true);
      void loadList();
    }, 600);
  };

  // ---- wiki-link autocomplete ---------------------------------------------

  const refreshWikiState = (value: string, cursor: number) => {
    const before = value.slice(0, cursor);
    const m = /\[\[([^\[\]\n]{0,60})$/.exec(before);
    setWiki(m ? { query: m[1], start: m.index, index: 0 } : null);
  };

  const insertWikiLink = (targetTitle: string) => {
    if (wiki === null || !textareaRef.current) return;
    const cursor = textareaRef.current.selectionStart;
    const next = `${draft.slice(0, wiki.start)}[[${targetTitle}]]${draft.slice(cursor)}`;
    setDraft(next);
    scheduleSave(title, next);
    setWiki(null);
    const pos = wiki.start + targetTitle.length + 4;
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(pos, pos);
    });
  };

  const onEditorKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (wiki === null || wikiMatches.length === 0) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const delta = e.key === "ArrowDown" ? 1 : -1;
      setWiki({ ...wiki, index: (wiki.index + delta + wikiMatches.length) % wikiMatches.length });
    } else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      insertWikiLink(wikiMatches[wiki.index].title);
    } else if (e.key === "Escape") {
      setWiki(null);
    }
  };

  // ---- source linking -----------------------------------------------------

  const linkSource = async (sourceId: string) => {
    if (!active) return;
    const updated = await api.updateNote(active.id, { source_id: sourceId });
    setActive({ ...active, source_id: updated.source_id });
  };

  const createSourceFromPage = async () => {
    if (!active || !active.source_url) return;
    const src = await api.createSource({
      title: active.source_title || active.title,
      url: active.source_url,
      kind: "article",
    });
    setSources((prev) => [src, ...prev]);
    await linkSource(src.id);
  };

  const createNew = async () => {
    const n = await api.createNote({ title: "Untitled", content: "" });
    await loadList();
    navigate(`/notes/${n.id}`);
  };

  const remove = async () => {
    if (!active) return;
    await api.deleteNote(active.id);
    await loadList();
    navigate("/notes");
  };

  return (
    <div className="flex h-full">
      <div className="w-72 shrink-0 border-r border-ink-800 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-ink-800">
          <h2 className="text-sm font-semibold">Notes</h2>
          <button
            onClick={() => void createNew()}
            className="rounded-md p-1.5 text-ink-300 hover:bg-ink-800 hover:text-ink-100 transition-colors"
            title="New note"
          >
            <Plus size={16} />
          </button>
        </div>
        <div className="overflow-y-auto">
          {notes.map((n) => (
            <button
              key={n.id}
              onClick={() => navigate(`/notes/${n.id}`)}
              className={clsx(
                "w-full text-left px-4 py-2.5 border-b border-ink-850",
                n.id === noteId ? "bg-ink-850" : "hover:bg-ink-900",
              )}
            >
              <span className="block text-sm truncate">{n.title || "Untitled"}</span>
              <span className="block text-[11px] text-ink-500 mt-0.5">
                {new Date(n.modified_at + "Z").toLocaleDateString()}
                {n.tags.length > 0 && (
                  <span className="ml-2 text-accent-400">{n.tags.map((t) => `#${t}`).join(" ")}</span>
                )}
              </span>
            </button>
          ))}
          {notes.length === 0 && (
            <p className="px-4 py-6 text-xs text-ink-500">No notes yet.</p>
          )}
        </div>
      </div>

      {active ? (
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="flex items-center gap-2 px-6 py-3 border-b border-ink-800">
            <input
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                scheduleSave(e.target.value, draft);
              }}
              className="flex-1 bg-transparent text-lg font-semibold outline-none"
              placeholder="Untitled"
            />
            <span className="text-[11px] text-ink-500 w-14">{saved ? "Saved" : "Saving…"}</span>
            <button
              onClick={() => setPreview((v) => !v)}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-ink-300 hover:bg-ink-800 transition-colors"
            >
              {preview ? <Pencil size={13} /> : <Eye size={13} />}
              {preview ? "Edit" : "Preview"}
            </button>
            <button
              onClick={() => void remove()}
              className="rounded-md p-1.5 text-ink-300 hover:bg-red-500/20 hover:text-red-400 transition-colors"
              title="Delete note"
            >
              <Trash2 size={14} />
            </button>
          </div>
          <div className="flex items-center gap-3 px-6 py-2 border-b border-ink-850 text-xs">
            {active.source_id ? (
              <span className="flex items-center gap-1.5 rounded-full bg-ink-800 px-2.5 py-1 text-ink-100">
                <BookMarked size={12} className="text-accent-400" />
                {sources.find((s) => s.id === active.source_id)?.title ?? "Source"}
                <button onClick={() => void linkSource("")}
                  className="text-ink-500 hover:text-red-400 transition-colors" title="Unlink source">
                  <X size={11} />
                </button>
              </span>
            ) : (
              <>
                <select
                  value=""
                  onChange={(e) => e.target.value && void linkSource(e.target.value)}
                  className="rounded-md border border-ink-700 bg-ink-850 px-2 py-1 text-xs text-ink-300 outline-none focus:border-accent-500"
                >
                  <option value="">Link source…</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>{s.title}</option>
                  ))}
                </select>
                {active.source_url && (
                  <button onClick={() => void createSourceFromPage()}
                    className="rounded-md px-2 py-1 text-ink-300 hover:bg-ink-800 transition-colors">
                    + New source from page
                  </button>
                )}
              </>
            )}
            {active.source_url && (
              <a href={active.source_url} target="_blank" rel="noreferrer"
                className="ml-auto flex items-center gap-1.5 text-accent-400 hover:underline truncate max-w-[45%]">
                <ExternalLink size={12} /> {active.source_title || active.source_url}
              </a>
            )}
          </div>
          {preview ? (
            <div className="flex-1 overflow-y-auto px-8 py-6 prose-md">
              <ReactMarkdown>{previewText}</ReactMarkdown>
            </div>
          ) : (
            <div className="relative flex-1 flex">
              <textarea
                ref={textareaRef}
                value={draft}
                onChange={(e) => {
                  setDraft(e.target.value);
                  scheduleSave(title, e.target.value);
                  refreshWikiState(e.target.value, e.target.selectionStart);
                }}
                onKeyDown={onEditorKeyDown}
                onClick={(e) =>
                  refreshWikiState(e.currentTarget.value, e.currentTarget.selectionStart)
                }
                onBlur={() => setTimeout(() => setWiki(null), 150)}
                className="flex-1 w-full bg-transparent px-8 py-6 outline-none resize-none font-mono text-[14px] leading-relaxed"
                placeholder="Write in Markdown…  Link other notes with [[Note Title]]"
              />
              {wiki !== null && wikiMatches.length > 0 && (
                <div className="absolute left-8 top-2 z-30 w-72 rounded-lg border border-ink-700 bg-ink-900 shadow-2xl overflow-hidden">
                  <p className="px-3 pt-2 pb-1 text-[10px] uppercase tracking-wide text-ink-500">
                    Link to note — ⏎ to insert
                  </p>
                  {wikiMatches.map((n, i) => (
                    <button
                      key={n.id}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        insertWikiLink(n.title);
                      }}
                      onMouseEnter={() => setWiki({ ...wiki, index: i })}
                      className={clsx(
                        "block w-full truncate px-3 py-1.5 text-left text-sm",
                        i === wiki.index ? "bg-ink-800 text-ink-100" : "text-ink-300",
                      )}
                    >
                      {n.title || "Untitled"}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {backlinks.length > 0 && (
            <div className="border-t border-ink-800 px-8 py-3">
              <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-ink-500 mb-2">
                <Link2 size={12} /> Linked from
              </p>
              <div className="flex flex-wrap gap-1.5">
                {backlinks.map((b) => (
                  <button
                    key={b.id}
                    onClick={() => navigate(`/notes/${b.id}`)}
                    className="rounded-full bg-ink-800 hover:bg-ink-700 px-3 py-1 text-xs text-ink-100 transition-colors"
                  >
                    {b.title || "Untitled"}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-sm text-ink-500">
          Select a note, or create one with +
        </div>
      )}
    </div>
  );
}
