from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..config import Settings
from ..deps import get_db, get_settings
from ..models import NoteIndex
from ..services import vault

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _to_out(settings: Settings, note: NoteIndex, with_content: bool = True) -> schemas.NoteOut:
    out = schemas.NoteOut.model_validate(note)
    if with_content:
        out.content = vault.read_content(settings, note)
    return out


def _get_or_404(db: Session, note_id: str) -> NoteIndex:
    note = db.get(NoteIndex, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("", response_model=list[schemas.NoteMeta])
def list_notes(
    kind: str | None = None,
    inbox: bool | None = None,
    project_id: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(NoteIndex).order_by(NoteIndex.modified_at.desc())
    if kind:
        stmt = stmt.where(NoteIndex.kind == kind)
    if inbox is not None:
        stmt = stmt.where(NoteIndex.inbox == inbox)
    if project_id:
        stmt = stmt.where(NoteIndex.project_id == project_id)
    notes = db.execute(stmt).scalars().all()
    if tag:
        notes = [n for n in notes if tag in (n.tags or [])]
    return notes


@router.get("/{note_id}", response_model=schemas.NoteOut)
def get_note(
    note_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return _to_out(settings, _get_or_404(db, note_id))


@router.post("", response_model=schemas.NoteOut, status_code=201)
def create_note(
    body: schemas.NoteCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    note = vault.create_note(db, settings, **body.model_dump())
    return _to_out(settings, note)


@router.patch("/{note_id}", response_model=schemas.NoteOut)
def update_note(
    note_id: str,
    body: schemas.NoteUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    note = _get_or_404(db, note_id)
    fields = body.model_dump(exclude_unset=True)
    content = fields.pop("content", None)
    note = vault.update_note(db, settings, note, content=content, **fields)
    return _to_out(settings, note)


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    vault.delete_note(db, settings, _get_or_404(db, note_id))
