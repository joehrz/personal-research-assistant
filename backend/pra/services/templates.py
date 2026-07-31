"""Note templates: plain Markdown files in ``vault/templates/``.

Users can edit or add templates with any editor; defaults are seeded on first
run. ``{{date}}`` and ``{{title}}`` placeholders are filled at creation time
(client- or server-side).
"""

from __future__ import annotations

from datetime import date

from ..config import Settings

DEFAULT_TEMPLATES: dict[str, str] = {
    "paper-summary": """# {{title}}

**Authors:**
**Venue / year:**
**Link / DOI:**

## TL;DR

## Key contributions
-

## Method

## Results

## Limitations & open questions
-

## Relevance to my work
""",
    "experiment-log": """# Experiment: {{title}}

**Date:** {{date}}
**Hypothesis:**

## Setup
- Data:
- Parameters:

## Procedure
1.

## Results

## Observations & anomalies

## Next steps
- [ ]
""",
    "meeting": """# Meeting: {{title}}

**Date:** {{date}}
**With:**

## Agenda
-

## Notes

## Decisions
-

## Action items
-
""",
    "daily": """# {{date}}

## Focus today

## Log

## Captured thoughts
""",
}


def seed_defaults(settings: Settings) -> None:
    """Write default templates that don't already exist (never overwrites)."""
    settings.ensure_dirs()
    for name, content in DEFAULT_TEMPLATES.items():
        path = settings.templates_dir / f"{name}.md"
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def list_templates(settings: Settings) -> list[dict]:
    settings.ensure_dirs()
    out = []
    for path in sorted(settings.templates_dir.glob("*.md")):
        out.append({"name": path.stem, "content": path.read_text(encoding="utf-8")})
    return out


def render(content: str, title: str = "", today: date | None = None) -> str:
    today = today or date.today()
    return content.replace("{{date}}", today.isoformat()).replace("{{title}}", title)


def get(settings: Settings, name: str) -> str | None:
    path = settings.templates_dir / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else None
