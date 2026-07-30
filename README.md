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
- **Projects** — lightweight containers created on the fly from `#project`.
- **Sources** — papers/articles/books with authors, URL, DOI, and reading status.
- **Search** — SQLite FTS5 full-text search across notes and tasks, in a
  Ctrl+K command palette with prefix (search-as-you-type) matching.

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

## Roadmap

Phase 2 adds the week calendar with drag-and-drop time blocking and Google
Calendar sync; Phase 3 adds wiki-links/backlinks, a browser clipper, and the
weekly review flow; Phase 4 adds semantic search and AI assistance. See
[docs/BRAINSTORM.md](docs/BRAINSTORM.md) for the full roadmap.
