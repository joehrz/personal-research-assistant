# Personal Research Assistant — Brainstorm & Vision

*A personal productivity app combining note-taking, task management, calendar/scheduling,
and project management, purpose-built for research and technical work.*

---

## 1. The Core Problem

Today the workflow looks like this: snippets of research material get pasted into Notepad,
tasks live somewhere else (or nowhere), and there's no connection between *what you're
learning*, *what you need to do*, and *when you'll do it*. Existing tools each solve one
slice:

- Note apps don't schedule.
- Task apps don't hold knowledge.
- Calendars don't know about either.
- Research tools (reference managers) don't manage your day.

**The big idea: one app where a piece of captured knowledge, a task, and a block of time
are all first-class citizens that can link to each other.** A snippet can spawn a task; a
task can be scheduled onto the calendar; a project ties all three together; and everything
is searchable from one place.

---

## 2. What's Already Out There (Market Scan, mid-2026)

### Notes / Personal Knowledge Management (PKM)
| Tool | What it does well | Where it falls short for us |
|------|-------------------|------------------------------|
| **Notion** | All-in-one workspace: notes, databases, wikis, light PM, built-in AI | Cloud-only, slow for quick capture, data lives on their servers |
| **Obsidian** | Local-first Markdown, bi-directional links, graph view, huge plugin ecosystem | Tasks/calendar only via plugins; no real scheduling engine |
| **Logseq** | Open-source outliner, bidirectional links, local files | Same gap: not a scheduler/PM tool |
| **Capacities** | Object-based notes with calendar/tasks integrated into a knowledge graph | Cloud-based, opinionated object model |
| **Anytype** | Local-first, object-based, encrypted sync | Young ecosystem, task features are basic |

Key philosophical divide in the market: **all-in-one cloud workspaces (Notion)** vs.
**local-first plain-file tools (Obsidian/Logseq)**. Local-first wins on speed, privacy,
and data ownership — a big deal for a personal tool holding years of research.

### Tasks / To-do
| Tool | What it does well | Gap |
|------|-------------------|-----|
| **Todoist** | Best-in-class natural-language entry ("call John next Monday 2pm p1"), clean, 150+ integrations | No knowledge layer; calendar is secondary |
| **TickTick** | Built-in calendar views, habits, Pomodoro, Eisenhower matrix — great value bundle | Notes are an afterthought |

### Calendar / Daily planners ("time-blocking" category)
| Tool | What it does well | Gap |
|------|-------------------|-----|
| **Akiflow** | Command-center that funnels tasks from many sources into one time-blocking dashboard | Aggregator, not a home for knowledge |
| **Morgen** | Multi-account calendar consolidation + drag-and-drop time blocking + AI planning | Calendar-first, thin on notes/tasks |
| **Motion / Sunsama / Amie** | AI auto-scheduling / mindful daily planning | Same: no knowledge base |

### Research-specific tools
- **Zotero**: the standard for collecting/citing papers; one-click capture via browser
  connector. But it's citation storage only — people run the actual research workflow
  elsewhere.
- **AI research platforms (Paperguide, Paperpal, etc.)**: chat-with-PDF, summaries,
  literature review helpers — but they're paper-centric, not day-planning tools.
- **Web clippers (Obsidian Clipper, ClipCite, Zotero Connector)**: researchers need
  *clean capture* (strip ads/nav), *citation/source extraction* (URL, author, date, DOI),
  and *annotation*. No single app owns capture + organize + schedule.

### The gap we're filling
Nobody combines **frictionless snippet capture with provenance** (where did this come
from?), **linked notes**, **real task management**, and **a real calendar** in one
local-first app. Akiflow/Morgen prove people pay for tasks+calendar unification;
Obsidian proves people love local Markdown knowledge bases. We're building the
intersection, tuned for one user's research workflow.

---

## 3. Big Ideas (Feature Pillars)

### Pillar A — Frictionless Capture (the Notepad replacement)
The #1 job: make saving a snippet *faster than opening Notepad*.
- **Global hotkey quick-capture window**: hit a key anywhere, paste/type, Enter, gone.
  Zero-friction; file it later (or never — search finds it).
- **Clipboard-aware capture**: auto-attach source metadata. If you copy from a browser,
  grab the URL, page title, and timestamp. Provenance is gold for research.
- **Inbox model**: everything captured lands in an Inbox. A daily/weekly triage flow
  turns raw snippets into filed notes, tasks, or trash. (GTD-style "capture now, organize
  later.")
- **Capture types**: text snippet, code snippet (with language detection + syntax
  highlighting), link/bookmark, image/screenshot, file attachment, quick task ("todo:"
  prefix auto-creates a task).
- Later: browser extension web clipper (clean Markdown + citation extraction), email-in
  address, mobile share sheet.

### Pillar B — Knowledge Base (notes that connect)
- **Markdown notes, stored as local files** — durable, greppable, portable, no lock-in.
- **Bi-directional links** (`[[wiki-links]]`) + backlinks panel: see every place a
  concept is referenced.
- **Tags + folders + projects**: multiple organizational axes; don't force one hierarchy.
- **Snippet-first design**: unlike Obsidian, treat small captures as first-class — a
  stream of clips that can later be merged into synthesis notes.
- **Source objects**: a paper/article/book is an entity (title, authors, URL/DOI, status:
  to-read/reading/read). Snippets and notes link to their source → instant "everything I
  took from this paper" view. (Lightweight Zotero, not a replacement.)
- **Full-text search everywhere**, instant, fuzzy, with filters (type, tag, project,
  date). Search is the primary retrieval mechanism.
- Later: graph view, daily notes, note templates (paper summary, meeting, experiment log).

### Pillar C — Tasks (a real task engine)
- **Natural-language entry** (Todoist's killer feature): "review CV paper draft friday
  2pm #thesis p1" → parsed into task + due date + project + priority.
- Subtasks, priorities, due dates vs. **scheduled dates** (when you'll *do* it — distinct
  from when it's *due*), recurring tasks.
- **Tasks link to notes/snippets/sources**: "Read this paper" carries the paper with it.
  A task can be created *from* a snippet in one keystroke.
- Views: Today, Upcoming, per-project Kanban board, and an "someday/backlog" list.

### Pillar D — Calendar & Scheduling
- **Week/day calendar with drag-and-drop time blocking**: drag a task onto Tuesday 10am
  → it's scheduled. Unscheduled-task sidebar next to the calendar (the Akiflow/Morgen
  pattern).
- **Today dashboard**: today's blocks + due tasks + inbox count + quick capture. The
  screen you open every morning.
- Two-way **external calendar sync** (Google/Outlook via CalDAV/APIs) so real meetings
  appear alongside work blocks. (Read-only first; two-way later.)
- Later: focus timer (Pomodoro) attached to a block, automatic time logging → "where did
  my week go" review, AI-assisted planning ("fit these 5 tasks into my free slots").

### Pillar E — Projects (lightweight PM, not Jira)
- A **project** is a container that unifies the other pillars: its notes, sources, tasks,
  milestones, and time spent in one view.
- Project dashboard: status, next actions, recent notes, upcoming deadlines.
- Milestones with dates (paper deadline, experiment completion) that appear on the
  calendar.
- Archive completed projects but keep them fully searchable.

### Pillar F — Review & Resurfacing (the sleeper feature)
Research notes rot. Combat it:
- **Weekly review flow**: guided pass over inbox, stale tasks, and active projects.
- **Resurfacing**: "you clipped this 3 months ago and never touched it" — spaced
  repetition for ideas, not flashcards.
- Later: AI summaries ("what did I work on this month"), connections suggestions
  ("this new snippet looks related to [[attention mechanisms]]").

### Pillar G — AI layer (later, but design for it)
Every 2026 competitor is adding AI. For a personal research tool the valuable ones are:
- Semantic search / "chat with my notes" (RAG over the knowledge base).
- Auto-tagging and auto-linking suggestions on capture.
- Paper/article summarization on clip.
- Planning assistant ("schedule my week").
Keep it optional and local-data-respecting: AI reads your vault, your vault never
becomes hostage to a cloud service.

---

## 4. Product Principles

1. **Local-first.** Data is yours: Markdown + SQLite on disk. Works offline. Sync is a
   feature, not a requirement. (Obsidian's model — the right one for a personal tool.)
2. **Capture must be instant.** If quick-capture takes >2 seconds, the app has failed at
   its core job.
3. **Everything links.** Note ↔ task ↔ event ↔ source ↔ project. The links are the moat.
4. **Keyboard-first.** Command palette (Cmd/Ctrl-K), NL task entry, shortcuts everywhere.
5. **One user, no bloat.** No collab, no permissions, no sharing — personal tool. This is
   a huge simplifier vs. commercial apps.
6. **Plain-text durability.** In 10 years, the notes must still open in any editor.

---

## 5. Architecture Sketch

### Recommended shape
- **Desktop app** (primary): the daily driver with global hotkey capture.
  - **Option 1 — Tauri (Rust core + web UI)**: light (~10MB), fast, native global
    hotkeys/tray; Rust backend is great for file watching + search indexing.
  - **Option 2 — Electron**: heavier but the most battle-tested (Obsidian, Notion,
    Slack); easiest ecosystem.
  - **Option 3 — Local web app** (e.g. FastAPI/Node backend + browser UI): simplest to
    build, but no global hotkey / tray — weakens Pillar A. Fine for a v0 spike.
  - *Leaning: Tauri, with React/TypeScript UI.*
- **Storage**:
  - Notes/snippets → **Markdown files with YAML frontmatter** in a "vault" folder
    (portable, git-friendly, editable elsewhere).
  - Tasks, events, links, sources, metadata → **SQLite** (relational data doesn't belong
    in Markdown).
  - **FTS5** (SQLite full-text search) index over everything; later add a vector index
    for semantic search.
- **Sync/backup**: the vault folder syncs via anything (git, Syncthing, Dropbox).
  SQLite can be rebuilt from files where possible; export everything to plain text.
- **Editor**: CodeMirror 6 or TipTap for Markdown editing with live preview.
- **Calendar sync**: Google Calendar API read-only first.

### Data model (first draft)
```
Note      { id, path, title, tags[], project?, created, modified }
Snippet   { = Note with kind:snippet, source_url?, source_title?, clipped_at }
Source    { id, title, authors[], url/doi, kind: paper|article|book|video, status }
Task      { id, title, notes, project?, priority, due_date?, scheduled_at?,
            duration_est?, recurrence?, status, parent_task? }
Event     { id, title, start, end, source: local|google, linked_task? }
Project   { id, name, status, color, milestones[] }
Link      { from_entity, to_entity, kind }   ← the glue table
```

---

## 6. Roadmap

### Phase 1 — "Better than Notepad" (MVP)
The moment it replaces Notepad + your current task list:
1. Vault setup, Markdown notes with editor + preview
2. Quick capture (global hotkey) → Inbox
3. Snippets with source-URL metadata; code snippets with highlighting
4. Basic tasks: create (incl. NL parsing for dates), complete, due dates, Today view
5. Full-text search across everything
6. Tags + projects (as simple containers)

### Phase 2 — "The planner"
7. Week calendar with drag-and-drop time blocking; unscheduled sidebar
8. Task ↔ note linking; create task from snippet
9. Google Calendar read-only sync
10. Recurring tasks, priorities, Kanban project view

### Phase 3 — "The research assistant"
11. Source entities + reading list; snippet→source linking
12. Bi-directional wiki-links + backlinks panel
13. Weekly review flow + resurfacing
14. Browser extension clipper

### Phase 4 — "The brain"
15. Semantic search / chat-with-notes (RAG)
16. AI planning, auto-tagging, summarization on clip
17. Time tracking + weekly analytics
18. Mobile capture (PWA or share-sheet companion)

---

## 7. Open Questions

1. **Platform**: Which OS(es) do you work on daily? (Determines Tauri/Electron packaging
   priorities and hotkey implementation.)
2. **Tech comfort**: Preferred stack? (TypeScript/React, Python, Rust…) — this is your
   app; you'll want to hack on it.
3. **Calendar provider**: Google, Outlook, or purely local calendar to start?
4. **What kind of research?** Academic papers (→ sources/DOI matter a lot) vs. general
   web/technical material (→ web clipper matters more)?
5. **Snippet volume**: dozens/day or a few/week? Affects how heavy the triage/inbox
   design needs to be.
6. **AI posture**: comfortable calling a cloud LLM API over your notes, or should AI
   features be local-only?
