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
  status: "todo" | "done";
  priority: number;
  tags: string[];
  due_date: string | null;
  scheduled_at: string | null;
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

export interface Note extends NoteMeta {
  content: string;
}

export interface Source {
  id: string;
  title: string;
  authors: string[];
  url: string;
  doi: string;
  kind: string;
  status: "to_read" | "reading" | "read";
  notes: string;
  created_at: string;
}

export interface SearchHit {
  entity_type: "note" | "task";
  entity_id: string;
  title: string;
  snippet: string;
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

  listNotes: (params: { kind?: string; inbox?: boolean; project_id?: string } = {}) =>
    request<NoteMeta[]>(`/api/notes${qs(params)}`),
  getNote: (id: string) => request<Note>(`/api/notes/${id}`),
  createNote: (body: Partial<Note>) =>
    request<Note>("/api/notes", { method: "POST", body: JSON.stringify(body) }),
  updateNote: (id: string, body: Partial<Note>) =>
    request<Note>(`/api/notes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteNote: (id: string) => request<void>(`/api/notes/${id}`, { method: "DELETE" }),

  listTasks: (view = "all", project_id?: string) =>
    request<Task[]>(`/api/tasks${qs({ view, project_id })}`),
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

  search: (q: string, types?: string) =>
    request<{ query: string; hits: SearchHit[] }>(`/api/search${qs({ q, types })}`),
};
