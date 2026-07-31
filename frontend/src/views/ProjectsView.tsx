import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { Archive, Plus } from "lucide-react";
import { api, type Project, type Task } from "../api";

const PALETTE = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899", "#8b5cf6"];

export default function ProjectsView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    const [p, t] = await Promise.all([api.listProjects(), api.listTasks("all")]);
    setProjects(p);
    setTasks(t);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async () => {
    if (!name.trim()) return;
    setError(null);
    try {
      await api.createProject(name.trim(), PALETTE[projects.length % PALETTE.length]);
      setName("");
      void load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const archive = async (p: Project) => {
    await api.updateProject(p.id, { status: "archived" });
    void load();
  };

  const openCount = (id: string) => tasks.filter((t) => t.project_id === id).length;

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <header className="mb-5">
        <h2 className="text-xl font-semibold">Projects</h2>
        <p className="text-sm text-ink-300 mt-1">
          Containers for related notes and tasks — reference them as <code className="font-mono bg-ink-800 rounded px-1">#project</code> in task entry.
        </p>
      </header>

      <div className="flex gap-2 mb-6">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void create()}
          placeholder="New project name…"
          className="flex-1 rounded-xl border border-ink-700 bg-ink-900 px-4 py-2.5 text-sm outline-none focus:border-accent-500 placeholder:text-ink-500 transition-colors"
        />
        <button
          onClick={() => void create()}
          className="flex items-center gap-1.5 rounded-xl bg-accent-500 hover:bg-accent-400 text-white text-sm font-medium px-4 transition-colors"
        >
          <Plus size={15} /> Add
        </button>
      </div>
      {error && <p className="-mt-4 mb-4 text-xs text-red-400">{error}</p>}

      <div className="grid grid-cols-2 gap-3">
        {projects.map((p) => (
          <div
            key={p.id}
            onClick={() => navigate(`/projects/${p.id}`)}
            className="group cursor-pointer rounded-xl border border-ink-800 bg-ink-900 p-4 hover:border-accent-500 transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <span className="h-3 w-3 rounded-full" style={{ backgroundColor: p.color }} />
              <span className="font-medium text-sm">{p.name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  void archive(p);
                }}
                title="Archive"
                className="ml-auto opacity-0 group-hover:opacity-100 text-ink-500 hover:text-ink-100 transition-all"
              >
                <Archive size={14} />
              </button>
            </div>
            <p className="mt-2 text-xs text-ink-500">{openCount(p.id)} open tasks · board →</p>
          </div>
        ))}
        {projects.length === 0 && (
          <p className="col-span-2 py-10 text-center text-sm text-ink-500">No projects yet.</p>
        )}
      </div>
    </div>
  );
}
