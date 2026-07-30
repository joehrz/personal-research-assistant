"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Projects -------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class ProjectUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    status: str | None = None


class ProjectOut(ORMModel):
    id: str
    name: str
    color: str
    status: str
    created_at: datetime


# ---- Tasks ----------------------------------------------------------------

class TaskCreate(BaseModel):
    """Either raw `text` (natural-language parsed) or explicit fields."""

    text: str | None = None
    title: str | None = None
    notes: str = ""
    priority: int | None = Field(default=None, ge=1, le=4)
    tags: list[str] = []
    due_date: date | None = None
    scheduled_at: datetime | None = None
    project_id: str | None = None
    parent_id: str | None = None
    note_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    status: str | None = None
    priority: int | None = Field(default=None, ge=1, le=4)
    tags: list[str] | None = None
    due_date: date | None = None
    clear_due_date: bool = False
    scheduled_at: datetime | None = None
    clear_scheduled_at: bool = False
    project_id: str | None = None
    clear_project: bool = False


class TaskOut(ORMModel):
    id: str
    title: str
    notes: str
    status: str
    priority: int
    tags: list[str]
    due_date: date | None
    scheduled_at: datetime | None
    project_id: str | None
    parent_id: str | None
    note_id: str | None
    created_at: datetime
    completed_at: datetime | None


# ---- Sources --------------------------------------------------------------

class SourceCreate(BaseModel):
    title: str
    authors: list[str] = []
    url: str = ""
    doi: str = ""
    kind: str = "article"
    status: str = "to_read"
    notes: str = ""


class SourceUpdate(BaseModel):
    title: str | None = None
    authors: list[str] | None = None
    url: str | None = None
    doi: str | None = None
    kind: str | None = None
    status: str | None = None
    notes: str | None = None


class SourceOut(ORMModel):
    id: str
    title: str
    authors: list[str]
    url: str
    doi: str
    kind: str
    status: str
    notes: str
    created_at: datetime


# ---- Notes ----------------------------------------------------------------

class NoteCreate(BaseModel):
    title: str = ""
    content: str = ""
    kind: str = "note"
    inbox: bool = False
    tags: list[str] = []
    language: str = ""
    source_url: str = ""
    source_title: str = ""
    source_id: str | None = None
    project_id: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    kind: str | None = None
    inbox: bool | None = None
    tags: list[str] | None = None
    language: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    source_id: str | None = None
    project_id: str | None = None


class NoteMeta(ORMModel):
    id: str
    path: str
    title: str
    kind: str
    inbox: bool
    tags: list[str]
    language: str
    source_url: str
    source_title: str
    source_id: str | None
    project_id: str | None
    created_at: datetime
    modified_at: datetime


class NoteOut(NoteMeta):
    content: str = ""


# ---- Capture --------------------------------------------------------------

class CaptureIn(BaseModel):
    text: str
    source_url: str = ""
    source_title: str = ""


class CaptureOut(BaseModel):
    kind: str  # "task" | "snippet"
    task: TaskOut | None = None
    note: NoteOut | None = None


# ---- Search ---------------------------------------------------------------

class SearchHit(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    snippet: str


class SearchOut(BaseModel):
    query: str
    hits: list[SearchHit]
