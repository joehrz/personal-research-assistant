"""Focus timer and time tracking.

One entry runs at a time; starting a new one stops the running one. The
summary endpoint powers "where did my week go" analytics.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import Project, Task, TimeEntry, now_local

router = APIRouter(prefix="/api/time", tags=["time"])


def _minutes(entry: TimeEntry, now: datetime) -> int:
    end = entry.ended_at or now
    return max(0, round((end - entry.started_at).total_seconds() / 60))


def _to_out(entry: TimeEntry, now: datetime) -> schemas.TimeEntryOut:
    out = schemas.TimeEntryOut.model_validate(entry)
    out.minutes = _minutes(entry, now)
    return out


def _running(db: Session) -> TimeEntry | None:
    return db.execute(
        select(TimeEntry).where(TimeEntry.ended_at.is_(None))
    ).scalars().first()


def _stop_running(db: Session) -> TimeEntry | None:
    entry = _running(db)
    if entry is not None:
        entry.ended_at = now_local()
    return entry


@router.post("/start", response_model=schemas.TimeEntryOut, status_code=201)
def start(body: schemas.TimeStartIn, db: Session = Depends(get_db)):
    _stop_running(db)
    label, project_id = body.label, None
    if body.task_id:
        task = db.get(Task, body.task_id)
        if task is not None:
            label = label or task.title
            project_id = task.project_id
    entry = TimeEntry(label=label or "Focus", task_id=body.task_id, project_id=project_id)
    db.add(entry)
    db.commit()
    return _to_out(entry, now_local())


@router.post("/stop", response_model=schemas.TimeEntryOut | None)
def stop(db: Session = Depends(get_db)):
    entry = _stop_running(db)
    db.commit()
    return _to_out(entry, now_local()) if entry else None


@router.get("/current", response_model=schemas.TimeEntryOut | None)
def current(db: Session = Depends(get_db)):
    entry = _running(db)
    return _to_out(entry, now_local()) if entry else None


@router.get("/entries", response_model=list[schemas.TimeEntryOut])
def entries(
    start: datetime = Query(),
    end: datetime = Query(),
    db: Session = Depends(get_db),
):
    now = now_local()
    rows = db.execute(
        select(TimeEntry)
        .where(TimeEntry.started_at >= start, TimeEntry.started_at < end)
        .order_by(TimeEntry.started_at.desc())
    ).scalars().all()
    return [_to_out(e, now) for e in rows]


@router.get("/summary", response_model=schemas.TimeSummaryOut)
def summary(
    start: datetime = Query(),
    end: datetime = Query(),
    db: Session = Depends(get_db),
):
    now = now_local()
    rows = db.execute(
        select(TimeEntry).where(TimeEntry.started_at >= start, TimeEntry.started_at < end)
    ).scalars().all()

    by_day: dict[str, int] = defaultdict(int)
    by_project: dict[str | None, int] = defaultdict(int)
    total = 0
    for e in rows:
        minutes = _minutes(e, now)
        total += minutes
        by_day[e.started_at.date().isoformat()] += minutes
        by_project[e.project_id] += minutes

    projects = {
        p.id: p for p in db.execute(select(Project)).scalars()
    }
    project_rows = []
    for pid, minutes in sorted(by_project.items(), key=lambda kv: -kv[1]):
        p = projects.get(pid)
        project_rows.append(
            schemas.TimeByProject(
                project_id=pid,
                project_name=p.name if p else "No project",
                color=p.color if p else "#55617d",
                minutes=minutes,
            )
        )
    return schemas.TimeSummaryOut(
        total_min=total,
        by_day=[
            schemas.TimeByDay(date=d, minutes=m) for d, m in sorted(by_day.items())
        ],
        by_project=project_rows,
    )
