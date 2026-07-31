from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..config import Settings
from ..deps import get_db, get_settings
from ..services import vault
from .notes import _to_out

router = APIRouter(prefix="/api/trash", tags=["trash"])


@router.get("", response_model=list[schemas.TrashItem])
def list_trash(settings: Settings = Depends(get_settings)):
    return vault.list_trash(settings)


@router.post("/{name}/restore", response_model=schemas.NoteOut)
def restore(
    name: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    note = vault.restore_from_trash(db, settings, name)
    if note is None:
        raise HTTPException(status_code=404, detail="Trash item not found")
    return _to_out(settings, note, db=db)


@router.delete("/{name}", status_code=204)
def purge(name: str, settings: Settings = Depends(get_settings)):
    if vault.purge_trash(settings, name=name) == 0:
        raise HTTPException(status_code=404, detail="Trash item not found")
