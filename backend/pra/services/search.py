"""Full-text search over notes and tasks via SQLite FTS5."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import NoteIndex, Task


def remove(session: Session, entity_type: str, entity_id: str) -> None:
    session.execute(
        text("DELETE FROM search_index WHERE entity_type = :t AND entity_id = :i"),
        {"t": entity_type, "i": entity_id},
    )


def _index(session: Session, entity_type: str, entity_id: str,
           title: str, body: str, tags: list[str]) -> None:
    remove(session, entity_type, entity_id)
    session.execute(
        text(
            "INSERT INTO search_index (entity_type, entity_id, title, body, tags) "
            "VALUES (:t, :i, :title, :body, :tags)"
        ),
        {"t": entity_type, "i": entity_id, "title": title, "body": body,
         "tags": " ".join(tags or [])},
    )


def index_note(session: Session, note: NoteIndex, content: str) -> None:
    body = content
    if note.source_title or note.source_url:
        body = f"{body}\n{note.source_title}\n{note.source_url}"
    _index(session, "note", note.id, note.title, body, note.tags or [])


def index_task(session: Session, task: Task) -> None:
    _index(session, "task", task.id, task.title, task.notes or "", task.tags or [])


def _escape_query(query: str) -> str:
    """Quote each term so user input can't break FTS5 syntax; AND semantics
    with prefix matching on the final term for search-as-you-type."""
    terms = [t.replace('"', '""') for t in query.split() if t.strip()]
    if not terms:
        return ""
    quoted = [f'"{t}"' for t in terms[:-1]] + [f'"{terms[-1]}"*']
    return " ".join(quoted)


def search(session: Session, query: str, entity_types: list[str] | None = None,
           limit: int = 30) -> list[dict]:
    fts_query = _escape_query(query)
    if not fts_query:
        return []
    sql = (
        "SELECT entity_type, entity_id, title, "
        "snippet(search_index, 3, '<mark>', '</mark>', ' … ', 18) AS snip, "
        "bm25(search_index) AS score "
        "FROM search_index WHERE search_index MATCH :q"
    )
    params: dict = {"q": fts_query, "limit": limit}
    if entity_types:
        placeholders = ",".join(f":et{i}" for i in range(len(entity_types)))
        sql += f" AND entity_type IN ({placeholders})"
        params.update({f"et{i}": t for i, t in enumerate(entity_types)})
    sql += " ORDER BY score LIMIT :limit"
    rows = session.execute(text(sql), params).all()
    return [
        {"entity_type": r.entity_type, "entity_id": r.entity_id,
         "title": r.title, "snippet": r.snip}
        for r in rows
    ]
