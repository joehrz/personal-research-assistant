import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Plus,
  Settings2,
  Trash2,
  X,
} from "lucide-react";
import clsx from "clsx";
import {
  api,
  type CalendarEvent,
  type CalendarFeed,
  type CalendarFeedError,
  type Task,
} from "../api";

const DAY_START = 6; // 06:00
const DAY_END = 22; // 22:00
const HOUR_PX = 48;
const SNAP_MIN = 30;
const PX_PER_MIN = HOUR_PX / 60;

const toLocalIso = (d: Date) => {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:00`;
};
const toDateStr = (d: Date) => toLocalIso(d).slice(0, 10);

const startOfWeek = (d: Date) => {
  const out = new Date(d);
  out.setHours(0, 0, 0, 0);
  out.setDate(out.getDate() - ((out.getDay() + 6) % 7)); // Monday
  return out;
};
const addDays = (d: Date, n: number) => {
  const out = new Date(d);
  out.setDate(out.getDate() + n);
  return out;
};

const minutesIntoDay = (iso: string) => {
  const d = new Date(iso);
  return d.getHours() * 60 + d.getMinutes();
};

/** Assign overlapping blocks to side-by-side lanes (like Google Calendar).
 * Returns per-id {col, cols}: the block's lane and its cluster's lane count. */
function layoutLanes(
  blocks: { id: string; startMin: number; endMin: number }[],
): Map<string, { col: number; cols: number }> {
  const sorted = [...blocks].sort(
    (a, b) => a.startMin - b.startMin || b.endMin - a.endMin,
  );
  const result = new Map<string, { col: number; cols: number }>();
  let cluster: string[] = [];
  let laneEnds: number[] = [];

  const flush = () => {
    for (const id of cluster) {
      result.get(id)!.cols = laneEnds.length;
    }
    cluster = [];
    laneEnds = [];
  };

  for (const b of sorted) {
    if (cluster.length > 0 && b.startMin >= Math.max(...laneEnds)) flush();
    let col = laneEnds.findIndex((end) => end <= b.startMin);
    if (col === -1) {
      col = laneEnds.length;
      laneEnds.push(b.endMin);
    } else {
      laneEnds[col] = b.endMin;
    }
    result.set(b.id, { col, cols: 1 });
    cluster.push(b.id);
  }
  flush();
  return result;
}

export default function CalendarView() {
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [scheduled, setScheduled] = useState<Task[]>([]);
  const [unscheduled, setUnscheduled] = useState<Task[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [feedErrors, setFeedErrors] = useState<CalendarFeedError[]>([]);
  const [feeds, setFeeds] = useState<CalendarFeed[]>([]);
  const [showFeeds, setShowFeeds] = useState(false);
  const [feedForm, setFeedForm] = useState({ name: "", url: "" });
  const gridRef = useRef<HTMLDivElement>(null);
  const resizing = useRef<{ id: string; startY: number; startDur: number } | null>(null);
  const [resizePreview, setResizePreview] = useState<{ id: string; dur: number } | null>(null);
  // Double-clicking an empty slot opens an inline "new block" form there.
  const [draft, setDraft] = useState<{ dayIso: string; minutes: number; title: string } | null>(null);

  const days = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart],
  );
  const weekEnd = useMemo(() => addDays(weekStart, 7), [weekStart]);

  const load = useCallback(async () => {
    const startIso = toLocalIso(weekStart);
    const endIso = toLocalIso(weekEnd);
    const [sched, all, ev, fds] = await Promise.all([
      api.listScheduledTasks(startIso, endIso),
      api.listTasks("all"),
      api.calendarEvents(startIso, endIso),
      api.listFeeds(),
    ]);
    setScheduled(sched);
    setUnscheduled(all.filter((t) => !t.scheduled_at));
    setEvents(ev.events);
    setFeedErrors(ev.errors);
    setFeeds(fds);
  }, [weekStart, weekEnd]);

  useEffect(() => {
    void load();
  }, [load]);

  // ---- drag & drop ---------------------------------------------------------

  const onDropOnDay = async (e: React.DragEvent, day: Date) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData("text/task-id");
    if (!taskId) return;
    const col = e.currentTarget as HTMLElement;
    const y = e.clientY - col.getBoundingClientRect().top;
    let minutes = DAY_START * 60 + Math.round(y / PX_PER_MIN / SNAP_MIN) * SNAP_MIN;
    minutes = Math.max(DAY_START * 60, Math.min(minutes, DAY_END * 60 - SNAP_MIN));
    const when = new Date(day);
    when.setHours(Math.floor(minutes / 60), minutes % 60, 0, 0);
    const task = [...scheduled, ...unscheduled].find((t) => t.id === taskId);
    await api.updateTask(taskId, {
      scheduled_at: toLocalIso(when),
      ...(task && !task.due_date ? { due_date: toDateStr(when) } : {}),
    });
    void load();
  };

  const startDrag = (e: React.DragEvent, task: Task) => {
    e.dataTransfer.setData("text/task-id", task.id);
    e.dataTransfer.effectAllowed = "move";
  };

  // ---- create a block in place --------------------------------------------

  const openDraft = (e: React.MouseEvent, day: Date) => {
    const col = e.currentTarget as HTMLElement;
    const y = e.clientY - col.getBoundingClientRect().top;
    let minutes = DAY_START * 60 + Math.floor(y / PX_PER_MIN / SNAP_MIN) * SNAP_MIN;
    minutes = Math.max(DAY_START * 60, Math.min(minutes, DAY_END * 60 - 60));
    setDraft({ dayIso: toDateStr(day), minutes, title: "" });
  };

  const saveDraft = async () => {
    if (!draft || !draft.title.trim()) {
      setDraft(null);
      return;
    }
    const when = new Date(draft.dayIso + "T00:00:00");
    when.setHours(Math.floor(draft.minutes / 60), draft.minutes % 60, 0, 0);
    await api.createTask({
      title: draft.title.trim(),
      scheduled_at: toLocalIso(when),
      due_date: draft.dayIso,
      duration_min: 60,
    });
    setDraft(null);
    void load();
  };

  // ---- resize --------------------------------------------------------------

  useEffect(() => {
    const move = (e: PointerEvent) => {
      if (!resizing.current) return;
      const { id, startY, startDur } = resizing.current;
      const dur = Math.max(
        SNAP_MIN,
        Math.round((startDur + (e.clientY - startY) / PX_PER_MIN) / SNAP_MIN) * SNAP_MIN,
      );
      setResizePreview({ id, dur });
    };
    const up = async () => {
      if (!resizing.current) return;
      const { id, startDur } = resizing.current;
      const preview = resizePreview?.id === id ? resizePreview.dur : startDur;
      resizing.current = null;
      setResizePreview(null);
      if (preview !== startDur) {
        await api.updateTask(id, { duration_min: preview });
        void load();
      }
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
  }, [resizePreview, load]);

  // ---- actions -------------------------------------------------------------

  const unschedule = async (task: Task) => {
    await api.updateTask(task.id, { clear_scheduled_at: true });
    void load();
  };
  const toggleDone = async (task: Task) => {
    await api.updateTask(task.id, { status: task.status === "done" ? "todo" : "done" });
    void load();
  };
  const addFeed = async () => {
    if (!feedForm.name.trim() || !feedForm.url.trim()) return;
    await api.createFeed({ name: feedForm.name.trim(), url: feedForm.url.trim() });
    setFeedForm({ name: "", url: "" });
    void load();
  };

  // ---- render helpers ------------------------------------------------------

  const gridHeight = (DAY_END - DAY_START) * HOUR_PX;
  const now = new Date();
  const nowTop = (now.getHours() * 60 + now.getMinutes() - DAY_START * 60) * PX_PER_MIN;

  const blockStyle = (startIso: string, durationMin: number) => {
    const top = (minutesIntoDay(startIso) - DAY_START * 60) * PX_PER_MIN;
    return {
      top: Math.max(0, top),
      height: Math.max(18, Math.min(durationMin * PX_PER_MIN, gridHeight - top)),
    };
  };

  const weekLabel = `${days[0].toLocaleDateString(undefined, { month: "short", day: "numeric" })} – ${days[6].toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}`;

  return (
    <div className="flex h-full">
      {/* Unscheduled sidebar */}
      <div className="w-64 shrink-0 border-r border-ink-800 flex flex-col">
        <div className="px-4 py-3 border-b border-ink-800">
          <h3 className="text-sm font-semibold">Unscheduled</h3>
          <p className="text-[11px] text-ink-500 mt-0.5">
            Drag a task onto the week — or double-click any empty slot to create one there.
          </p>
        </div>
        <div className="overflow-y-auto p-2 space-y-1.5">
          {unscheduled.map((t) => (
            <div
              key={t.id}
              draggable
              onDragStart={(e) => startDrag(e, t)}
              className="cursor-grab active:cursor-grabbing rounded-lg border border-ink-800 bg-ink-900 px-3 py-2 text-[13px] hover:border-accent-500 transition-colors"
            >
              <span className="block truncate">{t.title}</span>
              {t.due_date && (
                <span className="text-[11px] text-ink-500">
                  due {new Date(t.due_date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </span>
              )}
            </div>
          ))}
          {unscheduled.length === 0 && (
            <p className="px-2 py-6 text-xs text-ink-500">Everything is scheduled 🎉</p>
          )}
        </div>
      </div>

      {/* Calendar */}
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="flex items-center gap-2 px-5 py-3 border-b border-ink-800">
          <h2 className="text-base font-semibold">{weekLabel}</h2>
          <div className="ml-4 flex items-center gap-1">
            <button onClick={() => setWeekStart(addDays(weekStart, -7))}
              className="rounded-md p-1.5 text-ink-300 hover:bg-ink-800 transition-colors"><ChevronLeft size={16} /></button>
            <button onClick={() => setWeekStart(startOfWeek(new Date()))}
              className="rounded-md px-2.5 py-1 text-xs text-ink-300 hover:bg-ink-800 transition-colors">Today</button>
            <button onClick={() => setWeekStart(addDays(weekStart, 7))}
              className="rounded-md p-1.5 text-ink-300 hover:bg-ink-800 transition-colors"><ChevronRight size={16} /></button>
          </div>
          {feedErrors.length > 0 && (
            <span className="text-[11px] text-red-400">
              {feedErrors.map((e) => `${e.feed_name}: feed error`).join(" · ")}
            </span>
          )}
          <button
            onClick={() => setShowFeeds((v) => !v)}
            className="ml-auto flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-ink-300 hover:bg-ink-800 transition-colors"
          >
            <Settings2 size={13} /> Calendars
          </button>
        </div>

        {showFeeds && (
          <div className="border-b border-ink-800 bg-ink-900 px-5 py-3 space-y-2">
            {feeds.map((f) => (
              <div key={f.id} className="flex items-center gap-2 text-xs">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: f.color }} />
                <span className="font-medium">{f.name}</span>
                <span className="text-ink-500 truncate max-w-[360px]">{f.url}</span>
                <button
                  onClick={() => api.updateFeed(f.id, { enabled: !f.enabled }).then(load)}
                  className={clsx("ml-auto rounded-full px-2 py-0.5", f.enabled ? "bg-emerald-400/10 text-emerald-400" : "bg-ink-800 text-ink-500")}
                >
                  {f.enabled ? "on" : "off"}
                </button>
                <button onClick={() => api.deleteFeed(f.id).then(load)}
                  className="text-ink-500 hover:text-red-400 transition-colors"><Trash2 size={13} /></button>
              </div>
            ))}
            <div className="flex gap-2 pt-1">
              <input
                value={feedForm.name}
                onChange={(e) => setFeedForm({ ...feedForm, name: e.target.value })}
                placeholder="Name (e.g. Google)"
                className="w-40 rounded-md border border-ink-700 bg-ink-850 px-2.5 py-1.5 text-xs outline-none focus:border-accent-500"
              />
              <input
                value={feedForm.url}
                onChange={(e) => setFeedForm({ ...feedForm, url: e.target.value })}
                placeholder="ICS URL — in Google Calendar: Settings → your calendar → 'Secret address in iCal format'"
                className="flex-1 rounded-md border border-ink-700 bg-ink-850 px-2.5 py-1.5 text-xs outline-none focus:border-accent-500"
              />
              <button onClick={() => void addFeed()}
                className="flex items-center gap-1 rounded-md bg-accent-500 hover:bg-accent-400 text-white text-xs font-medium px-3 transition-colors">
                <Plus size={13} /> Add
              </button>
            </div>
          </div>
        )}

        {/* Day headers + all-day chips */}
        <div className="flex border-b border-ink-800 pl-14 pr-3">
          {days.map((day) => {
            const isToday = toDateStr(day) === toDateStr(new Date());
            const allDay = events.filter((e) => e.all_day && toDateStr(new Date(e.start)) === toDateStr(day));
            return (
              <div key={day.toISOString()} className="flex-1 min-w-0 px-1 py-2 text-center">
                <span className={clsx("text-xs font-medium", isToday ? "text-accent-400" : "text-ink-300")}>
                  {day.toLocaleDateString(undefined, { weekday: "short" })}{" "}
                  <span className={clsx(isToday && "rounded-full bg-accent-500 text-white px-1.5 py-0.5")}>
                    {day.getDate()}
                  </span>
                </span>
                {allDay.map((e, i) => (
                  <div key={i} className="mt-1 truncate rounded px-1.5 py-0.5 text-[10px] font-medium"
                    style={{ backgroundColor: `${e.color}26`, color: e.color }}>
                    {e.title}
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        {/* Time grid */}
        <div className="flex-1 overflow-y-auto" ref={gridRef}>
          <div className="flex pl-2 pr-3">
            {/* hour gutter */}
            <div className="w-12 shrink-0 relative" style={{ height: gridHeight }}>
              {Array.from({ length: DAY_END - DAY_START }, (_, i) => (
                <span key={i} className="absolute right-2 -translate-y-1/2 text-[10px] text-ink-500"
                  style={{ top: i * HOUR_PX }}>
                  {i + DAY_START === 12 ? "12pm" : i + DAY_START > 12 ? `${i + DAY_START - 12}pm` : `${i + DAY_START}am`}
                </span>
              ))}
            </div>
            {days.map((day) => {
              const isToday = toDateStr(day) === toDateStr(new Date());
              const dayEvents = events.filter(
                (e) => !e.all_day && toDateStr(new Date(e.start)) === toDateStr(day),
              );
              const dayTasks = scheduled.filter(
                (t) => t.scheduled_at && toDateStr(new Date(t.scheduled_at)) === toDateStr(day),
              );
              // Overlapping meetings/tasks share the column side-by-side.
              const lanes = layoutLanes([
                ...dayEvents.map((e, i) => {
                  const start = minutesIntoDay(e.start);
                  const dur = Math.max(15, (new Date(e.end).getTime() - new Date(e.start).getTime()) / 60000);
                  return { id: `ev-${i}`, startMin: start, endMin: start + dur };
                }),
                ...dayTasks.map((t) => {
                  const start = minutesIntoDay(t.scheduled_at!);
                  const dur = resizePreview?.id === t.id ? resizePreview.dur : t.duration_min;
                  return { id: t.id, startMin: start, endMin: start + dur };
                }),
              ]);
              const laneStyle = (id: string) => {
                const lane = lanes.get(id) ?? { col: 0, cols: 1 };
                return {
                  left: `calc(${(lane.col / lane.cols) * 100}% + 2px)`,
                  width: `calc(${100 / lane.cols}% - 4px)`,
                };
              };
              return (
                <div
                  key={day.toISOString()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => void onDropOnDay(e, day)}
                  onDoubleClick={(e) => openDraft(e, day)}
                  className="flex-1 min-w-0 relative border-l border-ink-850"
                  style={{ height: gridHeight }}
                >
                  {draft?.dayIso === toDateStr(day) && (
                    <div
                      className="absolute inset-x-0.5 z-30 rounded-md border border-accent-400 bg-ink-900 p-1.5 shadow-xl"
                      style={{ top: (draft.minutes - DAY_START * 60) * PX_PER_MIN }}
                    >
                      <input
                        autoFocus
                        value={draft.title}
                        onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") void saveDraft();
                          if (e.key === "Escape") setDraft(null);
                        }}
                        onBlur={() => void saveDraft()}
                        placeholder="What are you doing? ⏎"
                        className="w-full bg-transparent text-[12px] outline-none placeholder:text-ink-500"
                      />
                    </div>
                  )}
                  {Array.from({ length: DAY_END - DAY_START }, (_, i) => (
                    <div key={i} className="absolute inset-x-0 border-t border-ink-850"
                      style={{ top: i * HOUR_PX }} />
                  ))}
                  {isToday && nowTop >= 0 && nowTop <= gridHeight && (
                    <div className="absolute inset-x-0 z-20 border-t-2 border-red-400/80 pointer-events-none"
                      style={{ top: nowTop }} />
                  )}

                  {dayEvents.map((e, i) => {
                    const dur = Math.max(15, (new Date(e.end).getTime() - new Date(e.start).getTime()) / 60000);
                    return (
                      <div key={`ev-${i}`}
                        className="absolute z-0 rounded-md border-l-2 px-1.5 py-0.5 overflow-hidden"
                        style={{
                          ...blockStyle(e.start, dur),
                          ...laneStyle(`ev-${i}`),
                          backgroundColor: `${e.color}1f`,
                          borderColor: e.color,
                        }}
                        title={`${e.title}${e.location ? ` · ${e.location}` : ""}`}
                      >
                        <span className="block truncate text-[11px] font-medium" style={{ color: e.color }}>
                          {e.title}
                        </span>
                      </div>
                    );
                  })}

                  {dayTasks.map((t) => {
                    const dur = resizePreview?.id === t.id ? resizePreview.dur : t.duration_min;
                    return (
                      <div
                        key={t.id}
                        draggable
                        onDragStart={(e) => startDrag(e, t)}
                        className={clsx(
                          "group absolute z-10 rounded-md border-l-2 border-accent-400 bg-accent-500/25 px-1.5 py-0.5 overflow-hidden cursor-grab active:cursor-grabbing",
                          t.status === "done" && "opacity-50",
                        )}
                        style={{ ...blockStyle(t.scheduled_at!, dur), ...laneStyle(t.id) }}
                      >
                        <div className="flex items-start gap-1">
                          <button onClick={() => void toggleDone(t)} className="mt-0.5 shrink-0">
                            {t.status === "done"
                              ? <CheckCircle2 size={11} className="text-emerald-400" />
                              : <Circle size={11} className="text-accent-400" />}
                          </button>
                          <span className={clsx("min-w-0 truncate text-[11px] font-medium text-ink-100", t.status === "done" && "line-through")}>
                            {t.title}
                          </span>
                          <button onClick={() => void unschedule(t)}
                            className="ml-auto shrink-0 opacity-0 group-hover:opacity-100 text-ink-300 hover:text-red-400 transition-all"
                            title="Unschedule">
                            <X size={11} />
                          </button>
                        </div>
                        <div
                          onPointerDown={(e) => {
                            e.preventDefault();
                            resizing.current = { id: t.id, startY: e.clientY, startDur: t.duration_min };
                          }}
                          className="absolute inset-x-0 bottom-0 h-1.5 cursor-ns-resize opacity-0 group-hover:opacity-100 bg-accent-400/60"
                        />
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
