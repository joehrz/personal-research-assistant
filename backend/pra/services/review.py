"""Weekly review & resurfacing: one aggregate view of what needs attention.

- stale tasks: overdue for more than a few days, or dateless and untouched
  for weeks — the ones that silently rot in every task app
- resurfaced notes: a small random sample of old notes, so past research
  keeps coming back instead of being write-only
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import NoteIndex, Project, Task

STALE_OVERDUE_DAYS = 3
STALE_DATELESS_DAYS = 21
RESURFACE_AFTER_DAYS = 45
RESURFACE_COUNT = 5


def stale_tasks(session: Session, today: date | None = None) -> list[Task]:
    today = today or date.today()
    overdue_cutoff = today - timedelta(days=STALE_OVERDUE_DAYS)
    created_cutoff = datetime.combine(today - timedelta(days=STALE_DATELESS_DAYS),
                                      datetime.min.time())
    stmt = (
        select(Task)
        .where(
            Task.status == "todo",
            (Task.due_date < overdue_cutoff)
            | (Task.due_date.is_(None) & (Task.created_at < created_cutoff)),
        )
        .order_by(Task.due_date.is_(None), Task.due_date, Task.created_at)
    )
    return session.execute(stmt).scalars().all()


def resurfaced_notes(session: Session, now: datetime | None = None) -> list[NoteIndex]:
    now = now or datetime.now()
    cutoff = now - timedelta(days=RESURFACE_AFTER_DAYS)
    stmt = (
        select(NoteIndex)
        .where(NoteIndex.inbox.is_(False), NoteIndex.modified_at < cutoff)
        .order_by(func.random())
        .limit(RESURFACE_COUNT)
    )
    return session.execute(stmt).scalars().all()


def build_review(session: Session) -> dict:
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    completed_last_7 = session.execute(
        select(func.count()).select_from(Task).where(
            Task.status == "done", Task.completed_at >= week_ago
        )
    ).scalar_one()
    captured_last_7 = session.execute(
        select(func.count()).select_from(NoteIndex).where(NoteIndex.created_at >= week_ago)
    ).scalar_one()
    inbox_count = session.execute(
        select(func.count()).select_from(NoteIndex).where(NoteIndex.inbox.is_(True))
    ).scalar_one()
    open_tasks = session.execute(
        select(func.count()).select_from(Task).where(Task.status == "todo")
    ).scalar_one()

    projects = []
    for project in session.execute(
        select(Project).where(Project.status == "active").order_by(Project.created_at)
    ).scalars():
        count = session.execute(
            select(func.count()).select_from(Task).where(
                Task.project_id == project.id, Task.status == "todo"
            )
        ).scalar_one()
        projects.append({"project": project, "open_tasks": count})

    return {
        "completed_last_7": completed_last_7,
        "captured_last_7": captured_last_7,
        "inbox_count": inbox_count,
        "open_tasks": open_tasks,
        "stale_tasks": stale_tasks(session),
        "resurfaced": resurfaced_notes(session),
        "projects": projects,
    }
