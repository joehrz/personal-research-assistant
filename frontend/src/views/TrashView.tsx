import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ArchiveRestore, Trash2 } from "lucide-react";
import { api, type TrashItem } from "../api";

export default function TrashView() {
  const [items, setItems] = useState<TrashItem[]>([]);
  const navigate = useNavigate();

  const load = useCallback(async () => setItems(await api.listTrash()), []);

  useEffect(() => {
    void load();
  }, [load]);

  const restore = async (item: TrashItem) => {
    const note = await api.restoreTrash(item.name);
    navigate(`/notes/${note.id}`);
  };

  const purge = async (item: TrashItem) => {
    await api.purgeTrash(item.name);
    void load();
  };

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <header className="mb-6">
        <h2 className="flex items-center gap-2 text-xl font-semibold">
          <Trash2 size={18} className="text-ink-300" /> Trash
        </h2>
        <p className="text-sm text-ink-300 mt-1">
          Deleted notes are kept for 30 days, then purged automatically.
        </p>
      </header>

      {items.length === 0 ? (
        <p className="py-10 text-center text-sm text-ink-500">Trash is empty.</p>
      ) : (
        <div className="space-y-1">
          {items.map((item) => (
            <div key={item.name} className="flex items-center gap-3 rounded-lg border border-ink-800 bg-ink-900 px-3 py-2.5">
              <span className="min-w-0 truncate text-sm">{item.title}</span>
              {item.deleted_at && (
                <span className="text-[11px] text-ink-500 shrink-0">
                  deleted {new Date(item.deleted_at + "Z").toLocaleDateString()}
                </span>
              )}
              <span className="ml-auto flex items-center gap-1.5 shrink-0">
                <button onClick={() => void restore(item)}
                  className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-ink-300 hover:bg-ink-700 hover:text-ink-100 transition-colors">
                  <ArchiveRestore size={13} /> Restore
                </button>
                <button onClick={() => void purge(item)} title="Delete forever"
                  className="rounded-md p-1.5 text-ink-500 hover:text-red-400 transition-colors">
                  <Trash2 size={13} />
                </button>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
