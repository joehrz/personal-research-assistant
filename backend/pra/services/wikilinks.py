"""Wiki-links between notes: ``[[Target Title]]`` or ``[[Target Title|label]]``.

Links are resolved to note ids by (case-insensitive) title at save/reindex
time and stored in the generic ``links`` table with kind ``wikilink``. Because
the *resolved id* is stored, renaming the target note does not break existing
links. Unresolved targets are simply skipped and re-checked on the next save
or reindex, so forward references start working once the target note exists.
"""

from __future__ import annotations

import re

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import Link, NoteIndex

WIKILINK_RE = re.compile(r"\[\[([^\[\]|\n]+?)(?:\|([^\[\]\n]+?))?\]\]")

KIND = "wikilink"


def extract(content: str) -> list[tuple[str, str]]:
    """Return (target_title, display_label) pairs, in order of appearance."""
    out: list[tuple[str, str]] = []
    for m in WIKILINK_RE.finditer(content):
        target = m.group(1).strip()
        label = (m.group(2) or target).strip()
        if target:
            out.append((target, label))
    return out


def resolve(session: Session, title: str) -> NoteIndex | None:
    return session.execute(
        select(NoteIndex).where(func.lower(NoteIndex.title) == title.lower())
    ).scalars().first()


def update_for_note(session: Session, note: NoteIndex, content: str) -> None:
    """Rebuild this note's outgoing wikilink rows from its content."""
    session.execute(
        delete(Link).where(
            Link.from_type == "note", Link.from_id == note.id, Link.kind == KIND
        )
    )
    seen: set[str] = set()
    for target_title, _label in extract(content):
        target = resolve(session, target_title)
        if target is None or target.id == note.id or target.id in seen:
            continue
        seen.add(target.id)
        session.add(
            Link(from_type="note", from_id=note.id, to_type="note", to_id=target.id, kind=KIND)
        )


def outgoing(session: Session, note: NoteIndex) -> list[NoteIndex]:
    """Notes this note links to."""
    return session.execute(
        select(NoteIndex)
        .join(Link, Link.to_id == NoteIndex.id)
        .where(Link.from_type == "note", Link.from_id == note.id, Link.kind == KIND)
    ).scalars().all()


def backlinks(session: Session, note_id: str) -> list[NoteIndex]:
    """Notes that link to this note."""
    return session.execute(
        select(NoteIndex)
        .join(Link, Link.from_id == NoteIndex.id)
        .where(Link.to_type == "note", Link.to_id == note_id, Link.kind == KIND)
        .order_by(NoteIndex.modified_at.desc())
    ).scalars().all()


def remove_all(session: Session, note_id: str) -> None:
    """Drop link rows in both directions when a note is deleted."""
    session.execute(
        delete(Link).where(
            Link.kind == KIND,
            ((Link.from_type == "note") & (Link.from_id == note_id))
            | ((Link.to_type == "note") & (Link.to_id == note_id)),
        )
    )
