import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import {
  AlarmClockOff,
  CheckCircle2,
  HardDriveDownload,
  History,
  Inbox,
  Sparkles,
  Timer,
  Trash2,
} from "lucide-react";
import { api, type BackupStatus, type Review, type TimeSummary } from "../api";

const hoursLabel = (min: number) =>
  min >= 60 ? `${(min / 60).toFixed(1).replace(/\.0$/, "")}h` : `${min}m`;

function localIso(d: Date) {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T00:00:00`;
}

/** Last-7-days focus time: one bar per day plus a per-project breakdown. */
function TimeSection({ summary }: { summary: TimeSummary }) {
  const days: { date: string; label: string; minutes: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const iso = localIso(d).slice(0, 10);
    days.push({
      date: iso,
      label: d.toLocaleDateString(undefined, { weekday: "short" }),
      minutes: summary.by_day.find((x) => x.date === iso)?.minutes ?? 0,
    });
  }
  const maxDay = Math.max(60, ...days.map((d) => d.minutes));
  const maxProject = Math.max(1, ...summary.by_project.map((p) => p.minutes));

  return (
    <section className="mb-8">
      <h3 className="flex items-center gap-2 text-sm font-semibold mb-1">
        <Timer size={15} className="text-accent-400" /> Where did my week go
      </h3>
      <p className="text-xs text-ink-500 mb-3">
        {hoursLabel(summary.total_min)} of tracked focus in the last 7 days
      </p>
      <div className="rounded-xl border border-ink-800 bg-ink-900 p-4">
        <div className="flex items-end gap-2" style={{ height: 96 }} role="img"
          aria-label="Focus minutes per day, last 7 days">
          {days.map((d) => (
            <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full"
              title={`${d.label}: ${hoursLabel(d.minutes)}`}>
              {d.minutes > 0 && (
                <span className="text-[10px] text-ink-500 mb-1">{hoursLabel(d.minutes)}</span>
              )}
              <div
                className="w-full max-w-8 rounded-t bg-accent-400/80 hover:bg-accent-400 transition-colors"
                style={{ height: Math.max(d.minutes > 0 ? 3 : 0, (d.minutes / maxDay) * 64) }}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-2 mt-1.5 border-t border-ink-850 pt-1.5">
          {days.map((d) => (
            <span key={d.date} className="flex-1 text-center text-[10px] text-ink-500">
              {d.label}
            </span>
          ))}
        </div>
        {summary.by_project.length > 0 && (
          <div className="mt-4 space-y-1.5">
            {summary.by_project.map((p) => (
              <div key={p.project_id ?? "none"} className="flex items-center gap-2"
                title={`${p.project_name}: ${hoursLabel(p.minutes)}`}>
                <span className="w-32 shrink-0 truncate text-xs text-ink-300">{p.project_name}</span>
                <div className="flex-1 h-2 rounded-full bg-ink-850 overflow-hidden">
                  <div className="h-full rounded-full"
                    style={{ width: `${(p.minutes / maxProject) * 100}%`, backgroundColor: p.color }} />
                </div>
                <span className="w-12 shrink-0 text-right text-[11px] text-ink-500 tabular-nums">
                  {hoursLabel(p.minutes)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

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
  const [timeSummary, setTimeSummary] = useState<TimeSummary | null>(null);
  const [backup, setBackup] = useState<BackupStatus | null>(null);
  const [backupMsg, setBackupMsg] = useState("");
  const navigate = useNavigate();

  const backUpNow = async () => {
    const r = await api.runBackup();
    setBackupMsg(r.message);
    setBackup(await api.backupStatus());
  };

  const load = useCallback(async () => {
    setReview(await api.getReview());
    const start = new Date();
    start.setDate(start.getDate() - 6);
    const end = new Date();
    end.setDate(end.getDate() + 1);
    setTimeSummary(await api.timeSummary(localIso(start), localIso(end)));
    setBackup(await api.backupStatus());
  }, []);

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

      {timeSummary && timeSummary.total_min > 0 && <TimeSection summary={timeSummary} />}

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

      {backup && backup.git_available && (
        <section className="mb-8">
          <div className="flex items-center gap-3 rounded-xl border border-ink-800 bg-ink-900 px-4 py-3">
            <HardDriveDownload size={16} className="text-accent-400 shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-medium">Vault backup</p>
              <p className="text-xs text-ink-500">
                {backup.commits} snapshot{backup.commits === 1 ? "" : "s"}
                {backup.last_backup &&
                  ` · last ${new Date(backup.last_backup).toLocaleString()}`}
                {backupMsg && <span className="ml-2 text-emerald-400">{backupMsg}</span>}
              </p>
            </div>
            <button onClick={() => void backUpNow()}
              className="ml-auto shrink-0 rounded-lg bg-ink-800 hover:bg-ink-700 px-3 py-1.5 text-xs text-ink-300 hover:text-ink-100 transition-colors">
              Back up now
            </button>
          </div>
        </section>
      )}

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
