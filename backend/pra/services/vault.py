"""Vault service: Markdown files with YAML frontmatter as the source of truth.

Every note is a ``.md`` file under the vault. The SQLite ``notes`` table is an
index over those files (plus the FTS mirror) and can always be rebuilt with
:func:`reindex`. Files edited outside the app are picked up on reindex, which
runs at startup.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import NoteIndex, new_id, utcnow
from . import search as search_service

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# Frontmatter keys we persist. Anything else in a hand-edited file is preserved
# on rewrite via the `extra` passthrough.
KNOWN_KEYS = {
    "id", "title", "kind", "inbox", "tags", "language",
    "source_url", "source_title", "source_id", "project_id",
    "created", "modified",
}


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    slug = re.sub(r"[\s_-]+", "-", slug)[:max_len].strip("-")
    return slug or "untitled"


def split_frontmatter(raw: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    try:
        meta = yaml.safe_load(m.group(1)) or {}
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError:
        meta = {}
    return meta, raw[m.end():]


def render_file(meta: dict, content: str) -> str:
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{front}\n---\n\n{content.rstrip()}\n"


def _note_dir(settings: Settings, inbox: bool) -> Path:
    return settings.inbox_dir if inbox else settings.notes_dir


def _unique_path(directory: Path, slug: str, note_id: str) -> Path:
    return directory / f"{slug}-{note_id[:8]}.md"


def _meta_from_note(note: NoteIndex) -> dict:
    meta: dict = {
        "id": note.id,
        "title": note.title,
        "kind": note.kind,
        "inbox": note.inbox,
        "tags": list(note.tags or []),
        "created": note.created_at.isoformat(timespec="seconds"),
        "modified": note.modified_at.isoformat(timespec="seconds"),
    }
    if note.language:
        meta["language"] = note.language
    if note.source_url:
        meta["source_url"] = note.source_url
    if note.source_title:
        meta["source_title"] = note.source_title
    if note.source_id:
        meta["source_id"] = note.source_id
    if note.project_id:
        meta["project_id"] = note.project_id
    return meta


def _write_note_file(settings: Settings, note: NoteIndex, content: str) -> None:
    path = settings.vault_dir / note.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_file(_meta_from_note(note), content), encoding="utf-8")


def read_content(settings: Settings, note: NoteIndex) -> str:
    path = settings.vault_dir / note.path
    if not path.exists():
        return ""
    _, content = split_frontmatter(path.read_text(encoding="utf-8"))
    return content.strip("\n")


def create_note(
    session: Session,
    settings: Settings,
    *,
    title: str = "",
    content: str = "",
    kind: str = "note",
    inbox: bool = False,
    tags: list[str] | None = None,
    language: str = "",
    source_url: str = "",
    source_title: str = "",
    source_id: str | None = None,
    project_id: str | None = None,
) -> NoteIndex:
    note_id = new_id()
    if not title:
        first_line = content.strip().splitlines()[0] if content.strip() else ""
        title = first_line.lstrip("# ").strip()[:80] or "Untitled"
    directory = _note_dir(settings, inbox)
    path = _unique_path(directory, slugify(title), note_id)
    note = NoteIndex(
        id=note_id,
        path=str(path.relative_to(settings.vault_dir)),
        title=title,
        kind=kind,
        inbox=inbox,
        tags=tags or [],
        language=language,
        source_url=source_url,
        source_title=source_title,
        source_id=source_id,
        project_id=project_id,
    )
    session.add(note)
    session.flush()  # apply column defaults (timestamps) before writing the file
    _write_note_file(settings, note, content)
    search_service.index_note(session, note, content)
    session.commit()
    return note


def update_note(
    session: Session,
    settings: Settings,
    note: NoteIndex,
    *,
    content: str | None = None,
    **fields,
) -> NoteIndex:
    if content is None:
        content = read_content(settings, note)

    old_path = settings.vault_dir / note.path
    for key, value in fields.items():
        if value is not None and hasattr(note, key):
            setattr(note, key, value)
    note.modified_at = utcnow()

    # Moving between inbox/ and notes/, or a title change, relocates the file.
    new_path = _unique_path(_note_dir(settings, note.inbox), slugify(note.title), note.id)
    note.path = str(new_path.relative_to(settings.vault_dir))
    if old_path.exists() and old_path != new_path:
        old_path.unlink()

    _write_note_file(settings, note, content)
    search_service.index_note(session, note, content)
    session.commit()
    return note


def delete_note(session: Session, settings: Settings, note: NoteIndex) -> None:
    path = settings.vault_dir / note.path
    if path.exists():
        path.unlink()
    search_service.remove(session, "note", note.id)
    session.delete(note)
    session.commit()


def reindex(session: Session, settings: Settings) -> int:
    """Rebuild the note index from the files on disk. Returns note count."""
    settings.ensure_dirs()
    seen_ids: set[str] = set()
    count = 0
    for path in sorted(settings.vault_dir.rglob("*.md")):
        rel = str(path.relative_to(settings.vault_dir))
        meta, content = split_frontmatter(path.read_text(encoding="utf-8"))
        note_id = str(meta.get("id") or new_id())
        if note_id in seen_ids:  # duplicated id in a copied file: mint a new one
            note_id = new_id()
        seen_ids.add(note_id)

        note = session.get(NoteIndex, note_id)
        if note is None:
            note = NoteIndex(id=note_id)
            session.add(note)
        note.path = rel
        note.title = str(meta.get("title") or path.stem)
        note.kind = str(meta.get("kind") or "note")
        note.inbox = bool(meta.get("inbox", rel.startswith("inbox")))
        tags = meta.get("tags") or []
        note.tags = [str(t) for t in tags] if isinstance(tags, list) else [str(tags)]
        note.language = str(meta.get("language") or "")
        note.source_url = str(meta.get("source_url") or "")
        note.source_title = str(meta.get("source_title") or "")
        note.source_id = meta.get("source_id")
        note.project_id = meta.get("project_id")
        for attr, key in (("created_at", "created"), ("modified_at", "modified")):
            raw = meta.get(key)
            if raw:
                try:
                    setattr(note, attr, datetime.fromisoformat(str(raw)))
                except ValueError:
                    pass
        search_service.index_note(session, note, content.strip("\n"))
        count += 1

    # Drop index rows whose files vanished.
    for note in session.execute(select(NoteIndex)).scalars():
        if note.id not in seen_ids:
            search_service.remove(session, "note", note.id)
            session.delete(note)
    session.commit()
    return count
