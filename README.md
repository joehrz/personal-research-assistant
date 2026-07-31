# Personal Research Assistant

A local-first productivity app for research and technical work: quick snippet
capture, Markdown notes, tasks with natural-language entry, projects, a reading
list of sources, and instant full-text search — all in one place, all stored on
your own disk.

**Docs:** [Vision & brainstorm](docs/BRAINSTORM.md) · [Phase 1 technical plan](docs/PLAN.md)

## What it does today (Phase 1)

- **Quick capture** — one box for everything. Plain text becomes an inbox
  snippet (with optional source URL); `todo: email advisor tomorrow p1 #phd`
  becomes a task. Leading code fences are detected as code snippets.
- **Inbox triage** — file snippets as notes, convert them to tasks, or delete.
- **Markdown notes** — stored as plain `.md` files with YAML frontmatter in a
  vault folder you can sync, grep, or edit in any editor; external edits are
  reindexed on startup.
- **Tasks** — natural-language entry (`friday 2pm`, `in 3 days`, `sep 1`,
  `p1`–`p4`, `#project`, `@tag`), Today/Upcoming/No-date/Done views, distinct
  due date vs. scheduled time.
- **Recurring tasks** — `every weekday 9am`, `every monday`, `every 2 weeks`,
  `daily`, `monthly`… Completing an occurrence keeps it as history and spawns
  the next one (catching up a backlog never piles up duplicates).
- **Projects** — lightweight containers created on the fly from `#project`.
- **Sources** — papers/articles/books with authors, URL, DOI, and reading status.
- **Search** — SQLite FTS5 full-text search across notes and tasks, in a
  Ctrl+K command palette with prefix (search-as-you-type) matching.
- **Calendar & time blocking** — a week view where you drag unscheduled tasks
  onto the grid to block time, drag blocks to reschedule, resize to change
  duration, and complete tasks in place. External calendars (Google, Outlook,
  etc.) appear read-only via their ICS feed URLs — no OAuth setup needed.
- **Browser clipper** — a Chrome/Edge extension (in `clipper/`) that saves the
  current selection or page to your inbox with the source URL and title
  attached; right-click, popup, or Alt+Shift+C. See
  [clipper/README.md](clipper/README.md).
- **Wiki-links & backlinks** — write `[[Note Title]]` (or `[[Note Title|label]]`)
  to link notes; typing `[[` pops up title autocomplete (arrows + Enter to
  insert). Links render as clickable in preview, every note shows a "Linked
  from" panel, and links are stored by id, so renaming a note doesn't break
  them.
- **Source ↔ note linking** — attach any note to a source from the editor (or
  create a source straight from a clipped page's URL); expanding a source in
  the Sources list shows everything you took from that paper/article.
- **Weekly review** — one screen showing the week's throughput, inbox backlog,
  stale tasks (overdue or dateless-and-forgotten) with quick actions, a few
  resurfaced old notes so past research resurfaces instead of rotting, and
  per-project open-task counts.

Data lives in `~/.personal-research-assistant/` (override with `PRA_DATA_DIR`):
`vault/` holds your Markdown files; `pra.db` is a rebuildable index.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite (FTS5)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Desktop shell (Windows):** pywebview + `keyboard` global hotkey

## Development

Backend (API on http://127.0.0.1:8734):

```bash
cd backend
pip install -e .[dev]
pytest                                   # run the test suite
uvicorn pra.main:create_app --factory --reload --port 8734
```

Frontend (dev server on http://localhost:5173, proxies /api to the backend):

```bash
cd frontend
npm install
npm run dev
```

## Desktop app (Windows)

```bash
cd frontend && npm run build             # build the UI once
cd ../backend && pip install -e .[desktop]
python ../desktop/main.py
```

This opens a native window and registers **Ctrl+Alt+Space** as a system-wide
quick-capture hotkey. The backend serves the built frontend itself, so only
one process runs.

## Keyboard shortcuts (in-app)

| Key | Action |
|-----|--------|
| `C` | Quick capture |
| `Ctrl+K` | Search palette |
| `Ctrl+Enter` | Save capture |
| `Esc` | Close dialogs |

## Connecting Google Calendar

In Google Calendar: **Settings → [your calendar] → Integrate calendar →
Secret address in iCal format**. Copy that URL, then in the app open
**Calendar → Calendars → Add** and paste it. Events appear read-only alongside
your task blocks. (Keep the URL private — anyone with it can read the
calendar.) Outlook and most other calendars offer an equivalent ICS URL.

## Roadmap

Done: Phase 1 (capture, notes, tasks, search), Phase 2 (week calendar with
time blocking, ICS calendar feeds, browser clipper), Phase 3 (wiki-links with
backlinks, weekly review/resurfacing), and Phase 4 (recurring tasks, wiki-link
autocomplete, source↔note linking). AI features are intentionally out of
scope. Candidate next features: focus timer with time tracking, note
templates, daily notes, mobile capture. See
[docs/BRAINSTORM.md](docs/BRAINSTORM.md) for the original brainstorm.
