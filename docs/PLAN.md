# Phase 1 Technical Plan — "Better than Notepad"

## Context

Building the MVP described in `BRAINSTORM.md`: a local-first personal research assistant
combining quick snippet capture, Markdown notes, tasks with natural-language entry, and
full-text search. Target platform is Windows desktop; primary developer is strongest in
Python; both academic sources (DOI) and general web capture matter.

## Stack decision

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **Python 3.11 + FastAPI + SQLAlchemy + SQLite** | Python is the dev's home turf; future AI/RAG, PDF parsing, and DOI metadata features are all Python-native. SQLite FTS5 gives instant full-text search with zero infra. |
| Note storage | **Markdown files + YAML frontmatter** in a vault folder | Durable, portable, greppable, git/Syncthing-friendly. SQLite is only an index/cache that can be rebuilt from files. |
| Frontend | **React + TypeScript + Vite + Tailwind CSS** | Web tech is what makes Notion/Obsidian look good; best-looking option available. |
| Desktop shell | **pywebview** window + `keyboard` lib for the global quick-capture hotkey (Windows) | Keeps the whole runtime Python; no Rust/Electron toolchain. Can swap to Tauri later without touching backend or UI. |

## Repository layout

```
backend/            FastAPI app (installable package `pra`)
  pra/
    config.py       settings: vault dir, db path (env-overridable)
    db.py           engine/session, FTS5 setup
    models.py       Project, Task, Source, NoteIndex, Link
    schemas.py      Pydantic request/response models
    services/
      vault.py      markdown+frontmatter read/write, reindex
      taskparse.py  natural-language task parsing (dates, #project, p1-p4, @tags)
      search.py     FTS5 queries across notes+tasks
    routers/        notes, tasks, projects, sources, capture, search
  tests/            pytest suite for services + API
frontend/           Vite + React + TS + Tailwind
  src/
    api/            typed API client
    views/          Inbox, Notes, Tasks, Projects, Sources
    components/     Layout, CommandPalette (Ctrl+K search), QuickCapture
desktop/
  main.py           starts uvicorn + pywebview window + global hotkey
docs/               BRAINSTORM.md, PLAN.md
```

## Core behaviors (Phase 1 scope)

1. **Capture** → `POST /capture`: raw text lands as an inbox note (kind `snippet`),
   optional `source_url`/`source_title`; `todo:` prefix creates a task instead.
   Code snippets get language detection via fence hints.
2. **Notes**: CRUD; each note is a `.md` file with frontmatter (`id, title, kind, tags,
   project, source_url, created, modified`). Startup reindex scans the vault so external
   edits are picked up.
3. **Tasks**: CRUD with NL parsing — `"review paper draft friday 2pm #thesis p1 @deep-work"`
   → title/due/scheduled/project/priority/tags. Views: today, upcoming, inbox, done.
   Distinct `due_date` vs `scheduled_at`.
4. **Projects**: simple containers (name, color, status) that notes and tasks reference.
5. **Sources**: papers/articles/books with `url`, `doi`, `authors`, reading `status`;
   snippets can link to a source (Phase 3 will deepen this).
6. **Search**: FTS5 across note content + task titles, with type/tag/project filters;
   surfaced in UI as a Ctrl+K command palette.

## Verification

- `cd backend && pip install -e .[dev] && pytest` — service + API tests (parsing,
  vault round-trip, capture routing, search).
- `cd frontend && npm install && npm run build` — type-checks and builds the UI.
- Dev run: `uvicorn pra.main:app --reload` + `npm run dev` (proxy to :8000).
- Windows desktop run: `python desktop/main.py` (opens window, registers Ctrl+Alt+Space
  quick capture).

## Phase 2 (built)

- **Week calendar** (`frontend/src/views/CalendarView.tsx`): drag unscheduled
  tasks onto the grid (30-min snap), drag blocks to move, resize the bottom
  edge to change `duration_min`, complete/unschedule in place, current-time
  line, all-day chips.
- **External calendars** via ICS feed subscriptions (`pra/services/calendars.py`,
  `pra/routers/calendar.py`): Google/Outlook "secret iCal address" URLs,
  recurring events expanded with `recurring-ical-events`, 5-min fetch cache,
  broken feeds reported as per-feed errors instead of failing the request.
  Chosen over the Google Calendar API deliberately: read-only sync with zero
  OAuth/cloud-console setup.
- **Task duration**: `tasks.duration_min` added via a tiny forward-only
  ALTER TABLE migration helper in `pra/db.py` (`_ensure_column`).
- **Browser clipper** (`clipper/`): Chrome/Edge MV3 extension — popup with
  editable clip + save-as-task, context-menu and Alt+Shift+C one-shot clips,
  posts to `/api/capture` on 127.0.0.1 with source URL/title. Backend CORS
  allows `chrome-extension://` origins.

## Phase 3 (built)

- **Wiki-links** (`pra/services/wikilinks.py`): `[[Title]]` / `[[Title|label]]`
  resolved case-insensitively to note ids at save/reindex time and stored in
  the `links` table (kind `wikilink`) — rename-safe because the id is stored.
  Reindex resolves in a second pass so cross-file links work regardless of
  file order. Endpoints: `NoteOut.links` (outgoing) and
  `GET /api/notes/{id}/backlinks`. Preview renders resolved links as
  navigation; a "Linked from" panel lists backlinks.
- **Weekly review** (`pra/services/review.py`, `GET /api/review`): 7-day
  throughput stats, inbox backlog, stale tasks (overdue > 3 days, or dateless
  and created > 21 days ago) with quick actions, resurfaced notes (non-inbox,
  untouched > 45 days, random 5 — "Still relevant ✓" bumps `modified_at` via
  an empty PATCH), and active-project open-task counts.

## Phase 4 (built) — no-AI direction confirmed

- **Recurring tasks** (`pra/services/recurrence.py`): NL phrases (`every day`,
  `weekdays`, `every monday`, `every 2 weeks`, `monthly`…) parsed into a
  canonical recurrence string on `Task.recurrence` (added via `_ensure_column`
  migration). Completing a recurring task keeps the completed row as history
  and spawns the next occurrence from `max(due, today)` — so clearing a
  backlog of missed occurrences never piles up duplicates. Time-of-day is
  preserved for scheduled recurring tasks.
- **Wiki-link autocomplete** (NotesView): typing `[[` opens a title
  suggestion panel (filter-as-you-type, arrows/Enter/Tab/Esc).
- **Source ↔ note linking**: notes can be linked to a source from the editor
  (dropdown, unlink chip, and one-click "New source from page" using the
  clip's URL/title); `GET /api/notes?source_id=` powers a per-source
  "everything from this paper" panel in SourcesView.

## Phase 5 (built)

- **Focus timer & time tracking** (`pra/routers/time.py`, `TimeEntry` model):
  start/stop/current endpoints (starting stops the running entry), entries
  stored in local wall-clock time to match `scheduled_at` day boundaries;
  `/api/time/summary` groups minutes by day and project for the Review
  screen's "where did my week go" bars. Sidebar TimerWidget polls + ticks;
  tasks get a ▶ start-focus button that inherits label/project.
- **Note templates** (`pra/services/templates.py`): editable Markdown files in
  `vault/templates/` (excluded from note reindexing); defaults seeded on
  startup, never overwritten; `{{date}}`/`{{title}}` placeholders.
- **Daily notes**: `POST /api/notes/daily/today` gets-or-creates today's note
  (kind `daily`, titled with the ISO date) from the `daily` template.
- **Mobile capture PWA**: `#/capture` full-screen capture route,
  `manifest.webmanifest` + minimal network-first service worker + generated
  icons; served over LAN with `--host 0.0.0.0` and installable via
  Add to Home Screen.

## Phase 6 (built)

- **DOI/arXiv autofill + BibTeX** (`pra/services/doi.py`): Crossref and arXiv
  metadata lookup with pure-function parsers (unit-tested offline);
  `POST /api/sources/lookup`, `GET /api/sources/export.bib` with de-duplicated
  citation keys (`kerbl2023splatting`, `…2`). Sources gain `year`/`venue`.
- **Asset uploads** (`pra/routers/assets.py`): paste images/files into the
  editor → stored under `vault/assets/<yyyy-mm>/`, served at `/vault-assets/…`
  (deliberately NOT `/assets`, which the built frontend bundle mount uses).
- **Trash** (vault service): delete moves the file to `<data>/trash/` with a
  timestamp prefix; list/restore/purge endpoints + Trash screen; 30-day
  auto-purge at startup.
- **Vault backup** (`pra/services/backup.py`): local git repo inside the
  vault, auto-commit on startup + manual "Back up now"; fails soft when git
  is absent.
- **Kanban boards**: task status gains `doing` (open views use
  `status != done`); `/projects/:id` board with drag-and-drop columns and the
  project's notes.
- **Graph view**: `GET /api/graph` (non-inbox notes + wikilink edges); canvas
  force-directed layout with hover-neighborhood highlighting, no external
  libraries.

## Explicitly deferred

AI/semantic search (skipped by decision), two-way calendar write-back,
email-in capture, task dependencies, encryption at rest.
