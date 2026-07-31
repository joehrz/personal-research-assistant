import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { ArrowLeft, StickyNote } from "lucide-react";
import clsx from "clsx";
import { api, type NoteMeta, type Project, type Task } from "../api";

const COLUMNS = [
  { key: "todo", label: "To do" },
  { key: "doing", label: "Doing" },
  { key: "done", label: "Done" },
] as const;

export default function ProjectBoardView() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [notes, setNotes] = useState<NoteMeta[]>([]);
  const [text, setText] = useState("");

  const load = useCallback(async () => {
    if (!projectId) return;
    const [projects, open, done, projectNotes] = await Promise.all([
      api.listProjects(),
      api.listTasks("all", projectId),
      api.listTasks("done", projectId),
      api.listNotes({ project_id: projectId }),
    ]);
    const p = projects.find((x) => x.id === projectId);
    if (!p) {
      navigate("/projects");
      return;
    }
    setProject(p);
    setTasks([...open, ...done.slice(0, 15)]);
    setNotes(projectNotes);
  }, [projectId, navigate]);

  useEffect(() => {
    void load();
  }, [load]);

  const add = async () => {
    if (!text.trim() || !projectId) return;
    await api.createTask({ text, project_id: projectId });
    setText("");
    void load();
  };

  const move = async (taskId: string, status: string) => {
    await api.updateTask(taskId, { status });
    void load();
  };

  if (!project) return null;

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <header className="mb-5">
        <button onClick={() => navigate("/projects")}
          className="mb-2 flex items-center gap-1.5 text-xs text-ink-500 hover:text-ink-100 transition-colors">
          <ArrowLeft size={13} /> All projects
        </button>
        <h2 className="flex items-center gap-2.5 text-xl font-semibold">
          <span className="h-3.5 w-3.5 rounded-full" style={{ backgroundColor: project.color }} />
          {project.name}
        </h2>
      </header>

      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && void add()}
        placeholder="Add a task to this project…"
        className="mb-5 w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-2.5 text-sm outline-none focus:border-accent-500 placeholder:text-ink-500 transition-colors"
      />

      <div className="grid grid-cols-3 gap-3">
        {COLUMNS.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col.key);
          return (
            <div
              key={col.key}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const id = e.dataTransfer.getData("text/task-id");
                if (id) void move(id, col.key);
              }}
              className="rounded-xl border border-ink-800 bg-ink-900/60 p-2.5 min-h-64"
            >
              <p className="px-1.5 pb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-500">
                {col.label} <span className="ml-1 font-normal">{colTasks.length}</span>
              </p>
              <div className="space-y-1.5">
                {colTasks.map((t) => (
                  <div
                    key={t.id}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("text/task-id", t.id)}
                    className={clsx(
                      "cursor-grab active:cursor-grabbing rounded-lg border border-ink-800 bg-ink-900 px-3 py-2 text-[13px] hover:border-accent-500 transition-colors",
                      t.status === "done" && "opacity-60 line-through",
                    )}
                  >
                    {t.title}
                    {t.due_date && t.status !== "done" && (
                      <span className="mt-0.5 block text-[11px] text-ink-500">
                        due {new Date(t.due_date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {notes.length > 0 && (
        <section className="mt-8">
          <h3 className="mb-2 text-sm font-semibold">Project notes</h3>
          <div className="flex flex-wrap gap-1.5">
            {notes.map((n) => (
              <button key={n.id} onClick={() => navigate(`/notes/${n.id}`)}
                className="flex items-center gap-1.5 rounded-full bg-ink-800 hover:bg-ink-700 px-3 py-1 text-xs text-ink-100 transition-colors">
                <StickyNote size={11} className="text-accent-400" />
                {n.title || "Untitled"}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
