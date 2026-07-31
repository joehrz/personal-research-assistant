// Typed client for the PRA backend API.

export interface Project {
  id: string;
  name: string;
  color: string;
  status: string;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  notes: string;
  status: "todo" | "doing" | "done";
  priority: number;
  tags: string[];
  due_date: string | null;
  scheduled_at: string | null;
  duration_min: number;
  recurrence: string;
  project_id: string | null;
  parent_id: string | null;
  note_id: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface NoteMeta {
  id: string;
  path: string;
  title: string;
  kind: "note" | "snippet";
  inbox: boolean;
  tags: string[];
  language: string;
  source_url: string;
  source_title: string;
  source_id: string | null;
  project_id: string | null;
  created_at: string;
  modified_at: string;
}

export interface LinkedNote {
  id: string;
  title: string;
}

export interface Note extends NoteMeta {
  content: string;
  links: LinkedNote[];
}

export interface Source {
  id: string;
  title: string;
  authors: string[];
  url: string;
  doi: string;
  year: number | null;
  venue: string;
  kind: string;
  status: "to_read" | "reading" | "read";
  notes: string;
  created_at: string;
}

export interface SourceLookup {
  title: string;
  authors: string[];
  year: number | null;
  venue: string;
  doi: string;
  url: string;
  kind: string;
}

export interface TrashItem {
  name: string;
  title: string;
  deleted_at: string | null;
}

export interface BackupStatus {
  git_available: boolean;
  initialized: boolean;
  last_backup: string | null;
  commits: number;
}

export interface Graph {
  nodes: { id: string; title: string; kind: string }[];
  edges: { from_id: string; to_id: string }[];
}

export interface SearchHit {
  entity_type: "note" | "task";
  entity_id: string;
  title: string;
  snippet: string;
}

export interface CalendarFeed {
  id: string;
  name: string;
  url: string;
  color: string;
  enabled: boolean;
  created_at: string;
}

export interface CalendarEvent {
  feed_id: string;
  feed_name: string;
  color: string;
  title: string;
  start: string;
  end: string;
  all_day: boolean;
  location: string;
}

export interface CalendarFeedError {
  feed_id: string;
  feed_name: string;
  message: string;
}

export interface TimeEntry {
  id: string;
  label: string;
  task_id: string | null;
  project_id: string | null;
  started_at: string;
  ended_at: string | null;
  minutes: number;
}

export interface TimeSummary {
  total_min: number;
  by_day: { date: string; minutes: number }[];
  by_project: { project_id: string | null; project_name: string; color: string; minutes: number }[];
}

export interface Template {
  name: string;
  content: string;
}

export interface ProjectStat {
  project: Project;
  open_tasks: number;
}

export interface Review {
  completed_last_7: number;
  captured_last_7: number;
  inbox_count: number;
  open_tasks: number;
  stale_tasks: Task[];
  resurfaced: NoteMeta[];
  projects: ProjectStat[];
}

export interface CaptureResult {
  kind: "task" | "snippet";
  task: Task | null;
  note: Note | null;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* not json */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

const qs = (params: Record<string, string | boolean | undefined>) => {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) search.set(k, String(v));
  }
  const s = search.toString();
  return s ? `?${s}` : "";
};

export const api = {
  capture: (text: string, source_url = "", source_title = "") =>
    request<CaptureResult>("/api/capture", {
      method: "POST",
      body: JSON.stringify({ text, source_url, source_title }),
    }),

  listNotes: (params: { kind?: string; inbox?: boolean; project_id?: string; source_id?: string } = {}) =>
    request<NoteMeta[]>(`/api/notes${qs(params)}`),
  getNote: (id: string) => request<Note>(`/api/notes/${id}`),
  getBacklinks: (id: string) => request<NoteMeta[]>(`/api/notes/${id}/backlinks`),
  createNote: (body: Partial<Note>) =>
    request<Note>("/api/notes", { method: "POST", body: JSON.stringify(body) }),
  updateNote: (id: string, body: Partial<Note>) =>
    request<Note>(`/api/notes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteNote: (id: string) => request<void>(`/api/notes/${id}`, { method: "DELETE" }),

  listTasks: (view = "all", project_id?: string) =>
    request<Task[]>(`/api/tasks${qs({ view, project_id })}`),
  listScheduledTasks: (start: string, end: string) =>
    request<Task[]>(`/api/tasks${qs({ view: "scheduled", start, end })}`),
  createTask: (body: { text?: string } & Partial<Task>) =>
    request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(body) }),
  updateTask: (id: string, body: Record<string, unknown>) =>
    request<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteTask: (id: string) => request<void>(`/api/tasks/${id}`, { method: "DELETE" }),

  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (name: string, color?: string) =>
    request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, ...(color ? { color } : {}) }),
    }),
  updateProject: (id: string, body: Partial<Project>) =>
    request<Project>(`/api/projects/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteProject: (id: string) => request<void>(`/api/projects/${id}`, { method: "DELETE" }),

  listSources: () => request<Source[]>("/api/sources"),
  createSource: (body: Partial<Source>) =>
    request<Source>("/api/sources", { method: "POST", body: JSON.stringify(body) }),
  updateSource: (id: string, body: Partial<Source>) =>
    request<Source>(`/api/sources/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteSource: (id: string) => request<void>(`/api/sources/${id}`, { method: "DELETE" }),

  listFeeds: () => request<CalendarFeed[]>("/api/calendar/feeds"),
  createFeed: (body: { name: string; url: string; color?: string }) =>
    request<CalendarFeed>("/api/calendar/feeds", { method: "POST", body: JSON.stringify(body) }),
  updateFeed: (id: string, body: Partial<CalendarFeed>) =>
    request<CalendarFeed>(`/api/calendar/feeds/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteFeed: (id: string) => request<void>(`/api/calendar/feeds/${id}`, { method: "DELETE" }),
  calendarEvents: (start: string, end: string) =>
    request<{ events: CalendarEvent[]; errors: CalendarFeedError[] }>(
      `/api/calendar/events${qs({ start, end })}`,
    ),

  getReview: () => request<Review>("/api/review"),

  startTimer: (body: { task_id?: string; label?: string }) =>
    request<TimeEntry>("/api/time/start", { method: "POST", body: JSON.stringify(body) }),
  stopTimer: () => request<TimeEntry | null>("/api/time/stop", { method: "POST" }),
  currentTimer: () => request<TimeEntry | null>("/api/time/current"),
  timeSummary: (start: string, end: string) =>
    request<TimeSummary>(`/api/time/summary${qs({ start, end })}`),

  listTemplates: () => request<Template[]>("/api/templates"),
  dailyToday: () => request<Note>("/api/notes/daily/today", { method: "POST" }),

  lookupSource: (query: string) =>
    request<SourceLookup>("/api/sources/lookup", { method: "POST", body: JSON.stringify({ query }) }),
  uploadAsset: async (file: File) => {
    const form = new FormData();
    form.append("file", file, file.name || "pasted.png");
    const res = await fetch("/api/assets", { method: "POST", body: form });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    return res.json() as Promise<{ url: string; markdown: string; is_image: boolean }>;
  },
  listTrash: () => request<TrashItem[]>("/api/trash"),
  restoreTrash: (name: string) =>
    request<Note>(`/api/trash/${encodeURIComponent(name)}/restore`, { method: "POST" }),
  purgeTrash: (name: string) =>
    request<void>(`/api/trash/${encodeURIComponent(name)}`, { method: "DELETE" }),
  backupStatus: () => request<BackupStatus>("/api/backup/status"),
  runBackup: () => request<{ ok: boolean; message: string }>("/api/backup/run", { method: "POST" }),
  getGraph: () => request<Graph>("/api/graph"),

  search: (q: string, types?: string) =>
    request<{ query: string; hits: SearchHit[] }>(`/api/search${qs({ q, types })}`),
};
