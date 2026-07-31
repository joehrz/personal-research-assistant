import { useCallback, useEffect, useState } from "react";
import { Circle, CheckCircle2, Trash2, CalendarDays, Clock } from "lucide-react";
import clsx from "clsx";
import { api, type Project, type Task } from "../api";

const VIEWS = [
  { key: "today", label: "Today" },
  { key: "upcoming", label: "Upcoming" },
  { key: "inbox", label: "No date" },
  { key: "all", label: "All" },
  { key: "done", label: "Done" },
] as const;

const PRIORITY_COLORS: Record<number, string> = {
  1: "text-red-400",
  2: "text-amber-400",
  3: "text-sky-400",
  4: "text-ink-500",
};

function dueLabel(d: string | null): { text: string; overdue: boolean } | null {
  if (!d) return null;
  const due = new Date(d + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((due.getTime() - today.getTime()) / 86_400_000);
  if (days < 0) return { text: `${-days}d overdue`, overdue: true };
  if (days === 0) return { text: "Today", overdue: false };
  if (days === 1) return { text: "Tomorrow", overdue: false };
  return { text: due.toLocaleDateString(undefined, { month: "short", day: "numeric" }), overdue: false };
}

export default function TasksView() {
  const [view, setView] = useState<(typeof VIEWS)[number]["key"]>("today");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [t, p] = await Promise.all([api.listTasks(view), api.listProjects()]);
    setTasks(t);
    setProjects(p);
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const projectName = (id: string | null) => projects.find((p) => p.id === id)?.name;
  const projectColor = (id: string | null) => projects.find((p) => p.id === id)?.color;

  const add = async () => {
    if (!text.trim()) return;
    setError(null);
    try {
      await api.createTask({ text });
      setText("");
      void load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const toggle = async (task: Task) => {
    await api.updateTask(task.id, { status: task.status === "done" ? "todo" : "done" });
    void load();
  };

  const remove = async (task: Task) => {
    await api.deleteTask(task.id);
    void load();
  };

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <header className="mb-5">
        <h2 className="text-xl font-semibold">Tasks</h2>
      </header>

      <div className="mb-4">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void add()}
          placeholder='Add a task… e.g. "review paper draft friday 2pm #thesis p1 @deep-work"'
          className="w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3 text-sm outline-none focus:border-accent-500 placeholder:text-ink-500 transition-colors"
        />
        {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
      </div>

      <div className="flex gap-1 mb-5">
        {VIEWS.map((v) => (
          <button
            key={v.key}
            onClick={() => setView(v.key)}
            className={clsx(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
              view === v.key
                ? "bg-ink-800 text-ink-100"
                : "text-ink-300 hover:bg-ink-850 hover:text-ink-100",
            )}
          >
            {v.label}
          </button>
        ))}
      </div>

      <div className="space-y-1">
        {tasks.length === 0 && (
          <p className="py-10 text-center text-sm text-ink-500">Nothing here.</p>
        )}
        {tasks.map((task) => {
          const due = dueLabel(task.due_date);
          return (
            <div
              key={task.id}
              className="group flex items-center gap-3 rounded-lg px-3 py-2.5 hover:bg-ink-900 transition-colors"
            >
              <button onClick={() => void toggle(task)} className="shrink-0">
                {task.status === "done" ? (
                  <CheckCircle2 size={18} className="text-emerald-400" />
                ) : (
                  <Circle size={18} className={PRIORITY_COLORS[task.priority]} />
                )}
              </button>
              <span
                className={clsx(
                  "min-w-0 truncate text-sm",
                  task.status === "done" && "line-through text-ink-500",
                )}
              >
                {task.title}
              </span>
              <span className="ml-auto flex items-center gap-2 shrink-0 text-[11px]">
                {task.tags.map((t) => (
                  <span key={t} className="text-ink-500">@{t}</span>
                ))}
                {projectName(task.project_id) && (
                  <span
                    className="rounded-full px-2 py-0.5 font-medium"
                    style={{
                      color: projectColor(task.project_id),
                      backgroundColor: `${projectColor(task.project_id)}22`,
                    }}
                  >
                    {projectName(task.project_id)}
                  </span>
                )}
                {task.scheduled_at && (
                  <span className="flex items-center gap-1 text-ink-300">
                    <Clock size={11} />
                    {new Date(task.scheduled_at).toLocaleTimeString(undefined, {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </span>
                )}
                {due && (
                  <span
                    className={clsx(
                      "flex items-center gap-1",
                      due.overdue ? "text-red-400" : "text-ink-300",
                    )}
                  >
                    <CalendarDays size={11} /> {due.text}
                  </span>
                )}
                <button
                  onClick={() => void remove(task)}
                  className="opacity-0 group-hover:opacity-100 text-ink-500 hover:text-red-400 transition-all"
                >
                  <Trash2 size={13} />
                </button>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
