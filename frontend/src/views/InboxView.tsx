import { useCallback, useEffect, useState } from "react";
import { ExternalLink, FileCheck, ListTodo, Trash2, Inbox as InboxIcon } from "lucide-react";
import { api, type Note, type NoteMeta } from "../api";

export default function InboxView() {
  const [items, setItems] = useState<NoteMeta[]>([]);
  const [contents, setContents] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    const metas = await api.listNotes({ inbox: true });
    setItems(metas);
    const loaded: Record<string, string> = {};
    await Promise.all(
      metas.map(async (m) => {
        const full: Note = await api.getNote(m.id);
        loaded[m.id] = full.content;
      }),
    );
    setContents(loaded);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const fileAsNote = async (id: string) => {
    await api.updateNote(id, { inbox: false, kind: "note" });
    void load();
  };

  const makeTask = async (item: NoteMeta) => {
    const text = contents[item.id] ?? item.title;
    await api.createTask({ title: text.split("\n")[0].slice(0, 200), note_id: item.id });
    await api.updateNote(item.id, { inbox: false });
    void load();
  };

  const remove = async (id: string) => {
    await api.deleteNote(id);
    void load();
  };

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <header className="mb-6">
        <h2 className="text-xl font-semibold">Inbox</h2>
        <p className="text-sm text-ink-300 mt-1">
          Captured snippets waiting for triage — file, convert, or discard.
        </p>
      </header>

      {items.length === 0 && (
        <div className="border border-dashed border-ink-700 rounded-xl py-16 text-center text-ink-500">
          <InboxIcon className="mx-auto mb-3" size={28} />
          <p className="text-sm">Inbox zero. Press <kbd className="font-mono bg-ink-800 rounded px-1.5 py-0.5 text-xs">C</kbd> to capture something.</p>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <article key={item.id} className="rounded-xl border border-ink-800 bg-ink-900 overflow-hidden">
            <div className="px-4 py-3">
              <pre className="whitespace-pre-wrap font-mono text-[13px] text-ink-100 max-h-48 overflow-y-auto">
                {contents[item.id] ?? "…"}
              </pre>
              {item.source_url && (
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1.5 text-xs text-accent-400 hover:underline"
                >
                  <ExternalLink size={12} />
                  {item.source_title || item.source_url}
                </a>
              )}
            </div>
            <div className="flex items-center gap-1.5 border-t border-ink-800 bg-ink-850 px-3 py-2 text-xs">
              <span className="text-ink-500 mr-auto">
                {new Date(item.created_at + "Z").toLocaleString()}
                {item.language && <span className="ml-2 font-mono text-accent-400">{item.language}</span>}
              </span>
              <button
                onClick={() => void fileAsNote(item.id)}
                className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-ink-300 hover:bg-ink-700 hover:text-ink-100 transition-colors"
              >
                <FileCheck size={13} /> File as note
              </button>
              <button
                onClick={() => void makeTask(item)}
                className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-ink-300 hover:bg-ink-700 hover:text-ink-100 transition-colors"
              >
                <ListTodo size={13} /> Make task
              </button>
              <button
                onClick={() => void remove(item.id)}
                className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-ink-300 hover:bg-red-500/20 hover:text-red-400 transition-colors"
              >
                <Trash2 size={13} /> Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
