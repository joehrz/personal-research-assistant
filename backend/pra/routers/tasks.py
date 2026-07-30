from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import Project, Task, utcnow
from ..services import search as search_service
from ..services import taskparse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_or_404(db: Session, task_id: str) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _resolve_project(db: Session, name: str) -> Project:
    project = db.execute(select(Project).where(Project.name == name)).scalar_one_or_none()
    if project is None:
        project = Project(name=name)
        db.add(project)
        db.flush()
    return project


@router.get("", response_model=list[schemas.TaskOut])
def list_tasks(
    view: str = "all",  # all | today | upcoming | inbox | done
    project_id: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Task)
    today = date.today()
    if view == "done":
        stmt = stmt.where(Task.status == "done").order_by(Task.completed_at.desc())
    else:
        stmt = stmt.where(Task.status == "todo")
        if view == "today":
            stmt = stmt.where(Task.due_date <= today)
        elif view == "upcoming":
            stmt = stmt.where(Task.due_date > today, Task.due_date <= today + timedelta(days=14))
        elif view == "inbox":
            stmt = stmt.where(Task.due_date.is_(None), Task.project_id.is_(None))
        stmt = stmt.order_by(
            Task.due_date.is_(None), Task.due_date, Task.priority, Task.created_at
        )
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=schemas.TaskOut, status_code=201)
def create_task(body: schemas.TaskCreate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    text = data.pop("text", None)
    if text:
        parsed = taskparse.parse(text)
        if not parsed.title:
            raise HTTPException(status_code=422, detail="Task text has no title")
        data.setdefault("title", parsed.title)
        data.setdefault("due_date", parsed.due_date)
        data.setdefault("scheduled_at", parsed.scheduled_at)
        if parsed.priority != 4:
            data.setdefault("priority", parsed.priority)
        if parsed.tags:
            data.setdefault("tags", parsed.tags)
        if parsed.project and "project_id" not in data:
            data["project_id"] = _resolve_project(db, parsed.project).id
    if not data.get("title"):
        raise HTTPException(status_code=422, detail="Task needs a title or text")
    data = {k: v for k, v in data.items() if v is not None}
    task = Task(**data)
    db.add(task)
    db.flush()
    search_service.index_task(db, task)
    db.commit()
    return task


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: str, body: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = _get_or_404(db, task_id)
    fields = body.model_dump(exclude_unset=True)

    if fields.pop("clear_due_date", False):
        task.due_date = None
        fields.pop("due_date", None)
    if fields.pop("clear_scheduled_at", False):
        task.scheduled_at = None
        fields.pop("scheduled_at", None)
    if fields.pop("clear_project", False):
        task.project_id = None
        fields.pop("project_id", None)

    status = fields.pop("status", None)
    if status is not None and status != task.status:
        task.status = status
        task.completed_at = utcnow() if status == "done" else None

    for key, value in fields.items():
        if value is not None:
            setattr(task, key, value)

    search_service.index_task(db, task)
    db.commit()
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = _get_or_404(db, task_id)
    search_service.remove(db, "task", task.id)
    db.delete(task)
    db.commit()
