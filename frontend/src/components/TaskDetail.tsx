import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ExternalLink, Trash2, X } from "lucide-react";
import { api, type NoteMeta, type Project, type Task } from "../api";

const PRIORITIES = [
  { value: 1, label: "P1 — urgent" },
  { value: 2, label: "P2 — high" },
  { value: 3, label: "P3 — normal" },
  { value: 4, label: "P4 — none" },
];

const WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/** Recurrence choices, anchored to the task's date where relevant. */
function recurrenceOptions(anchor: Date, current: string) {
  const weekday = (anchor.getDay() + 6) % 7; // JS Sunday=0 -> our Monday=0
  const options = [
    { value: "", label: "Does not repeat" },
    { value: "daily", label: "Every day" },
    { value: "weekdays", label: "Every weekday (Mon–Fri)" },
    { value: `weekly:${weekday}`, label: `Weekly on ${WEEKDAY_NAMES[weekday]}` },
    { value: "every:2:weeks", label: "Every 2 weeks" },
    { value: `monthly:${anchor.getDate()}`, label: `Monthly on day ${anchor.getDate()}` },
  ];
  if (current && !options.some((o) => o.value === current)) {
    options.push({ value: current, label: `Custom (${current})` });
  }
  return options;
}

export default function TaskDetail({
  task,
  projects,
  onClose,
  onChanged,
}: {
  task: Task;
  projects: Project[];
  onClose: () => void;
  onChanged: () => void;
}) {
  const navigate = useNavigate();
  const [notesList, setNotesList] = useState<NoteMeta[]>([]);
  const [title, setTitle] = useState(task.title);
  const [notes, setNotes] = useState(task.notes);
  const [priority, setPriority] = useState(task.priority);
  const [tags, setTags] = useState(task.tags.join(", "));
  const [projectId, setProjectId] = useState(task.project_id ?? "");
  const [due, setDue] = useState(task.due_date ?? "");
  const [scheduled, setScheduled] = useState(task.scheduled_at?.slice(0, 16) ?? "");
  const [duration, setDuration] = useState(task.duration_min);
  const [recurrence, setRecurrence] = useState(task.recurrence);
  const [noteId, setNoteId] = useState(task.note_id ?? "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.listNotes({ inbox: false }).then(setNotesList).catch(() => setNotesList([]));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const anchor = due ? new Date(due + "T00:00:00") : new Date();

  const save = async () => {
    if (!title.trim()) return;
    setSaving(true);
    try {
      await api.updateTask(task.id, {
        title: title.trim(),
        notes,
        priority,
        tags: tags.split(",").map((t) => t.trim().replace(/^@/, "")).filter(Boolean),
        recurrence,
        note_id: noteId, // "" unlinks
        ...(projectId ? { project_id: projectId } : { clear_project: true }),
        ...(due ? { due_date: due } : { clear_due_date: true }),
        ...(scheduled
          ? { scheduled_at: `${scheduled}:00`, duration_min: duration }
          : { clear_scheduled_at: true }),
      });
      onChanged();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    await api.deleteTask(task.id);
    onChanged();
    onClose();
  };

  const input =
    "w-full rounded-lg border border-ink-700 bg-ink-850 px-3 py-2 text-sm outline-none focus:border-accent-500 transition-colors";
  const label = "block text-[11px] uppercase tracking-wide text-ink-500 mb-1";

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="flex h-full w-[420px] max-w-[92vw] flex-col border-l border-ink-700 bg-ink-900 shadow-2xl">
        <div className="flex items-center gap-2 border-b border-ink-800 px-5 py-3">
          <h3 className="text-sm font-semibold">Edit task</h3>
          <button onClick={() => void remove()} title="Delete task"
            className="ml-auto rounded-md p-1.5 text-ink-500 hover:bg-red-500/20 hover:text-red-400 transition-colors">
            <Trash2 size={15} />
          </button>
          <button onClick={onClose}
            className="rounded-md p-1.5 text-ink-300 hover:bg-ink-800 transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          <div>
            <span className={label}>Title</span>
            <input className={input} value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          <div>
            <span className={label}>Notes</span>
            <textarea className={`${input} resize-y`} rows={3} value={notes}
              onChange={(e) => setNotes(e.target.value)} placeholder="Details, links, context…" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className={label}>Priority</span>
              <select className={input} value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}>
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <span className={label}>Project</span>
              <select className={input} value={projectId}
                onChange={(e) => setProjectId(e.target.value)}>
                <option value="">No project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <span className={label}>Tags (comma-separated)</span>
            <input className={input} value={tags} onChange={(e) => setTags(e.target.value)}
              placeholder="deep-work, reading" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className={label}>Due date</span>
              <input type="date" className={input} value={due}
                onChange={(e) => setDue(e.target.value)} />
            </div>
            <div>
              <span className={label}>Repeat</span>
              <select className={input} value={recurrence}
                onChange={(e) => setRecurrence(e.target.value)}>
                {recurrenceOptions(anchor, recurrence).map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className={label}>Scheduled (calendar)</span>
              <input type="datetime-local" className={input} value={scheduled}
                onChange={(e) => setScheduled(e.target.value)} />
            </div>
            <div>
              <span className={label}>Duration (min)</span>
              <input type="number" min={5} step={5} className={input} value={duration}
                onChange={(e) => setDuration(Math.max(5, Number(e.target.value) || 60))}
                disabled={!scheduled} />
            </div>
          </div>

          <div>
            <span className={label}>Linked note</span>
            <div className="flex items-center gap-2">
              <select className={input} value={noteId}
                onChange={(e) => setNoteId(e.target.value)}>
                <option value="">No linked note</option>
                {notesList.map((n) => (
                  <option key={n.id} value={n.id}>{n.title || "Untitled"}</option>
                ))}
              </select>
              {noteId && (
                <button onClick={() => navigate(`/notes/${noteId}`)} title="Open note"
                  className="shrink-0 rounded-md p-2 text-ink-300 hover:bg-ink-800 hover:text-accent-400 transition-colors">
                  <ExternalLink size={14} />
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 border-t border-ink-800 px-5 py-3">
          <button onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm text-ink-300 hover:bg-ink-800 transition-colors">
            Cancel
          </button>
          <button onClick={() => void save()} disabled={saving || !title.trim()}
            className="ml-auto rounded-lg bg-accent-500 px-5 py-2 text-sm font-medium text-white hover:bg-accent-400 disabled:opacity-50 transition-colors">
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
