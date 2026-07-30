"""Quick capture: one endpoint that routes raw text to the right place.

- ``todo: buy lab notebook friday`` -> a task (natural-language parsed)
- anything else                     -> a snippet note in the inbox
- a leading code fence (```py)      -> snippet tagged with its language
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..config import Settings
from ..deps import get_db, get_settings
from ..models import Task
from ..services import search as search_service
from ..services import taskparse, vault
from .notes import _to_out
from .tasks import _resolve_project

router = APIRouter(prefix="/api/capture", tags=["capture"])

TODO_PREFIX_RE = re.compile(r"^\s*(?:todo|task)\s*:\s*", re.IGNORECASE)
CODE_FENCE_RE = re.compile(r"^\s*```([\w+-]*)\s*\n")


@router.post("", response_model=schemas.CaptureOut, status_code=201)
def capture(
    body: schemas.CaptureIn,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Nothing to capture")

    todo_match = TODO_PREFIX_RE.match(text)
    if todo_match:
        parsed = taskparse.parse(text[todo_match.end():])
        if not parsed.title:
            raise HTTPException(status_code=422, detail="Task has no title")
        task = Task(
            title=parsed.title,
            priority=parsed.priority,
            tags=parsed.tags,
            due_date=parsed.due_date,
            scheduled_at=parsed.scheduled_at,
            notes=f"Captured from: {body.source_url}" if body.source_url else "",
        )
        if parsed.project:
            task.project_id = _resolve_project(db, parsed.project).id
        db.add(task)
        db.flush()
        search_service.index_task(db, task)
        db.commit()
        return schemas.CaptureOut(kind="task", task=schemas.TaskOut.model_validate(task))

    language = ""
    fence = CODE_FENCE_RE.match(text)
    if fence and fence.group(1):
        language = fence.group(1).lower()

    note = vault.create_note(
        db,
        settings,
        content=text,
        kind="snippet",
        inbox=True,
        language=language,
        source_url=body.source_url,
        source_title=body.source_title,
    )
    return schemas.CaptureOut(kind="snippet", note=_to_out(settings, note))
