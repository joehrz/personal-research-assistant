import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlarmClockOff,
  CheckCircle2,
  History,
  Inbox,
  Sparkles,
  Trash2,
} from "lucide-react";
import { api, type Review } from "../api";

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-xl border border-ink-800 bg-ink-900 px-4 py-3">
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-ink-500 mt-0.5">{label}</p>
    </div>
  );
}

export default function ReviewView() {
  const [review, setReview] = useState<Review | null>(null);
  const navigate = useNavigate();

  const load = useCallback(async () => setReview(await api.getReview()), []);

  useEffect(() => {
    void load();
  }, [load]);

  if (!review) return null;

  const todayIso = new Date().toISOString().slice(0, 10);

  const rescheduleToday = async (id: string) => {
    await api.updateTask(id, { due_date: todayIso });
    void load();
  };
  const complete = async (id: string) => {
    await api.updateTask(id, { status: "done" });
    void load();
  };
  const removeTask = async (id: string) => {
    await api.deleteTask(id);
    void load();
  };
  const markReviewed = async (id: string) => {
    await api.updateNote(id, {}); // empty update bumps modified_at
    void load();
  };

  return (
    <div className="max-w-3xl mx-auto px-8 py-8">
      <header className="mb-6">
        <h2 className="flex items-center gap-2 text-xl font-semibold">
          <Sparkles size={18} className="text-accent-400" /> Weekly review
        </h2>
        <p className="text-sm text-ink-300 mt-1">
          A guided pass over what happened, what's rotting, and what's worth remembering.
        </p>
      </header>

      <div className="grid grid-cols-4 gap-3 mb-8">
        <Stat value={review.completed_last_7} label="tasks done · 7 days" />
        <Stat value={review.captured_last_7} label="notes captured · 7 days" />
        <Stat value={review.open_tasks} label="open tasks" />
        <Stat value={review.inbox_count} label="in inbox" />
      </div>

      {review.inbox_count > 0 && (
        <button
          onClick={() => navigate("/")}
          className="mb-8 flex w-full items-center gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-300 hover:bg-amber-400/15 transition-colors"
        >
          <Inbox size={16} />
          {review.inbox_count} snippet{review.inbox_count === 1 ? "" : "s"} waiting for triage — go to Inbox
        </button>
      )}

      <section className="mb-8">
        <h3 className="flex items-center gap-2 text-sm font-semibold mb-3">
          <AlarmClockOff size={15} className="text-red-400" /> Stale tasks
          <span className="text-ink-500 font-normal">— overdue or forgotten</span>
        </h3>
        {review.stale_tasks.length === 0 ? (
          <p className="text-sm text-ink-500">Nothing stale. Clean plate.</p>
        ) : (
          <div className="space-y-1">
            {review.stale_tasks.map((t) => (
              <div key={t.id} className="flex items-center gap-3 rounded-lg border border-ink-800 bg-ink-900 px-3 py-2.5">
                <span className="min-w-0 truncate text-sm">{t.title}</span>
                <span className="text-[11px] text-red-400 shrink-0">
                  {t.due_date
                    ? `due ${new Date(t.due_date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" })}`
                    : "no date"}
                </span>
                <span className="ml-auto flex items-center gap-1.5 shrink-0">
                  <button onClick={() => void rescheduleToday(t.id)}
                    className="rounded-md px-2 py-1 text-[11px] text-ink-300 hover:bg-ink-700 transition-colors">
                    Do today
                  </button>
                  <button onClick={() => void complete(t.id)} title="Mark done"
                    className="text-ink-500 hover:text-emerald-400 transition-colors">
                    <CheckCircle2 size={15} />
                  </button>
                  <button onClick={() => void removeTask(t.id)} title="Delete"
                    className="text-ink-500 hover:text-red-400 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="mb-8">
        <h3 className="flex items-center gap-2 text-sm font-semibold mb-3">
          <History size={15} className="text-accent-400" /> Resurfaced notes
          <span className="text-ink-500 font-normal">— you wrote these a while ago</span>
        </h3>
        {review.resurfaced.length === 0 ? (
          <p className="text-sm text-ink-500">Nothing to resurface yet.</p>
        ) : (
          <div className="space-y-1">
            {review.resurfaced.map((n) => (
              <div key={n.id} className="flex items-center gap-3 rounded-lg border border-ink-800 bg-ink-900 px-3 py-2.5">
                <button onClick={() => navigate(`/notes/${n.id}`)}
                  className="min-w-0 truncate text-left text-sm hover:text-accent-400 transition-colors">
                  {n.title || "Untitled"}
                </button>
                <span className="text-[11px] text-ink-500 shrink-0">
                  {new Date(n.modified_at + "Z").toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                </span>
                <button onClick={() => void markReviewed(n.id)}
                  className="ml-auto shrink-0 rounded-md px-2 py-1 text-[11px] text-ink-300 hover:bg-ink-700 transition-colors">
                  Still relevant ✓
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 className="text-sm font-semibold mb-3">Active projects</h3>
        {review.projects.length === 0 ? (
          <p className="text-sm text-ink-500">No active projects.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {review.projects.map(({ project, open_tasks }) => (
              <div key={project.id} className="flex items-center gap-2.5 rounded-xl border border-ink-800 bg-ink-900 px-4 py-3">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: project.color }} />
                <span className="text-sm font-medium">{project.name}</span>
                <span className="ml-auto text-xs text-ink-500">{open_tasks} open</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
