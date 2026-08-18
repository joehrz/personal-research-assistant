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
- **Focus timer & time tracking** — start a timer from the sidebar or from any
  task's ▶ button (one runs at a time; starting another stops the first). The
  weekly Review shows "where did my week go": tracked hours per day and per
  project.
- **Note templates** — paper summary, experiment log, and meeting templates
  ship by default as editable Markdown files in `vault/templates/`; add your
  own `.md` files there and they appear in the new-from-template menu
  (`{{date}}`/`{{title}}` are filled in).
- **Daily notes** — one click opens today's note (created from the `daily`
  template on first open, idempotent after that).
- **Mobile capture (PWA)** — a phone-friendly capture page at `#/capture`,
  installable to your home screen. See below.
- **DOI / arXiv autofill & BibTeX export** — paste a DOI, arXiv id, or paper
  URL into the source form and fetch title/authors/year/venue from Crossref or
  arXiv (plain metadata APIs, no AI); export all sources as `sources.bib` for
  LaTeX.
- **Image & attachment paste** — paste a screenshot or file into the note
  editor; it's stored in `vault/assets/` (so it syncs/backs up with the vault)
  and embedded as Markdown.
- **Trash** — deleting a note moves it to a trash folder, restorable for 30
  days from the Trash screen, then purged automatically.
- **Automatic vault backup** — every startup snapshots the vault into a local
  git repository inside `vault/` (full history of every note, recoverable with
  plain git); "Back up now" lives on the Review screen.
- **Project boards** — click a project for a To do / Doing / Done Kanban board
  with drag-and-drop, plus that project's notes.
- **Graph view** — an interactive map of your notes and their wiki-links;
  hover to highlight a note's neighborhood, click to open it.
- **Task editor** — click any task title to open a full editor: title, notes,
  priority, tags, project, due date, calendar schedule + duration, recurrence,
  and a linked note.
- **System tray** — the app lives in the tray: closing the window hides it
  (hotkeys keep working), and the tray menu has Open / Quick capture / Snip /
  Back up / Quit. The vault also auto-backs-up every 4 hours while running
  (`PRA_BACKUP_INTERVAL_MIN` to change, 0 disables).
- **Snip to inbox** — press **Ctrl+Alt+S** anywhere: the Windows snip overlay
  opens, and whatever you snip lands in your inbox as a note with the
  screenshot embedded.
- **Calendar overlap lanes** — overlapping meetings/blocks render side-by-side
  instead of on top of each other.
- **Tags & filtering** — tag notes from the editor (comma-separated field);
  the notes list has a filter box (`#tag` filters by tag) and clickable tag
  chips with counts.
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

This opens a native window, puts an icon in the system tray, and registers two
system-wide hotkeys: **Ctrl+Alt+Space** (quick capture) and **Ctrl+Alt+S**
(snip a screenshot straight to the inbox). Closing the window hides the app to
the tray; quit from the tray menu. The backend serves the built frontend
itself, so only one process runs.

## Keyboard shortcuts (in-app)

| Key | Action |
|-----|--------|
| `C` | Quick capture |
| `Ctrl+K` | Search palette |
| `Ctrl+Enter` | Save capture |
| `Esc` | Close dialogs |

## Capturing from your phone

The app is an installable PWA with a dedicated capture screen. To use it from
your phone on your home network:

```bash
cd frontend && npm run build
cd ../backend && uvicorn pra.main:create_app --factory --host 0.0.0.0 --port 8734
```

Then open `http://<your-pc-ip>:8734/#/capture` on your phone and use your
browser's **Add to Home Screen** — it installs like an app that opens straight
on the capture screen. Only bind to `0.0.0.0` on networks you trust; the
regular desktop app keeps listening on localhost only.

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
