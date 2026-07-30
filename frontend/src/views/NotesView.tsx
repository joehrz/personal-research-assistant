import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { Eye, Pencil, Plus, Trash2, ExternalLink } from "lucide-react";
import clsx from "clsx";
import { api, type Note, type NoteMeta } from "../api";

export default function NotesView() {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const [notes, setNotes] = useState<NoteMeta[]>([]);
  const [active, setActive] = useState<Note | null>(null);
  const [draft, setDraft] = useState("");
  const [title, setTitle] = useState("");
  const [preview, setPreview] = useState(false);
  const [saved, setSaved] = useState(true);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const loadList = useCallback(async () => {
    setNotes(await api.listNotes({ inbox: false }));
  }, []);

  useEffect(() => {
    void loadList();
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
  }, [noteId, navigate]);

  // Debounced autosave.
  const scheduleSave = (nextTitle: string, nextContent: string) => {
    setSaved(false);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      if (!active) return;
      await api.updateNote(active.id, { title: nextTitle, content: nextContent });
      setSaved(true);
      void loadList();
    }, 600);
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
          {active.source_url && (
            <a
              href={active.source_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-6 py-2 text-xs text-accent-400 border-b border-ink-850 hover:underline"
            >
              <ExternalLink size={12} /> {active.source_title || active.source_url}
            </a>
          )}
          {preview ? (
            <div className="flex-1 overflow-y-auto px-8 py-6 prose-md">
              <ReactMarkdown>{draft}</ReactMarkdown>
            </div>
          ) : (
            <textarea
              value={draft}
              onChange={(e) => {
                setDraft(e.target.value);
                scheduleSave(title, e.target.value);
              }}
              className="flex-1 w-full bg-transparent px-8 py-6 outline-none resize-none font-mono text-[14px] leading-relaxed"
              placeholder="Write in Markdown…"
            />
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
