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
    duration_min: int | None = Field(default=None, ge=5, le=24 * 60)
    recurrence: str | None = None
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
    duration_min: int | None = Field(default=None, ge=5, le=24 * 60)
    recurrence: str | None = None  # "" clears
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
    duration_min: int
    recurrence: str
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


class LinkedNote(BaseModel):
    id: str
    title: str


class NoteOut(NoteMeta):
    content: str = ""
    links: list[LinkedNote] = []  # notes this note wiki-links to


# ---- Capture --------------------------------------------------------------

class CaptureIn(BaseModel):
    text: str
    source_url: str = ""
    source_title: str = ""


class CaptureOut(BaseModel):
    kind: str  # "task" | "snippet"
    task: TaskOut | None = None
    note: NoteOut | None = None


# ---- Calendar -------------------------------------------------------------

class CalendarFeedCreate(BaseModel):
    name: str
    url: str
    color: str = "#22c55e"


class CalendarFeedUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    color: str | None = None
    enabled: bool | None = None


class CalendarFeedOut(ORMModel):
    id: str
    name: str
    url: str
    color: str
    enabled: bool
    created_at: datetime


class CalendarEventOut(BaseModel):
    feed_id: str
    feed_name: str
    color: str
    title: str
    start: datetime
    end: datetime
    all_day: bool
    location: str = ""


class CalendarFeedError(BaseModel):
    feed_id: str
    feed_name: str
    message: str


class CalendarEventsOut(BaseModel):
    events: list[CalendarEventOut]
    errors: list[CalendarFeedError]


# ---- Search ---------------------------------------------------------------

class SearchHit(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    snippet: str


class SearchOut(BaseModel):
    query: str
    hits: list[SearchHit]


# ---- Time tracking --------------------------------------------------------

class TimeStartIn(BaseModel):
    task_id: str | None = None
    label: str = ""


class TimeEntryOut(ORMModel):
    id: str
    label: str
    task_id: str | None
    project_id: str | None
    started_at: datetime
    ended_at: datetime | None
    minutes: int = 0


class TimeByDay(BaseModel):
    date: str
    minutes: int


class TimeByProject(BaseModel):
    project_id: str | None
    project_name: str
    color: str
    minutes: int


class TimeSummaryOut(BaseModel):
    total_min: int
    by_day: list[TimeByDay]
    by_project: list[TimeByProject]


# ---- Templates ------------------------------------------------------------

class TemplateOut(BaseModel):
    name: str
    content: str


# ---- Review ---------------------------------------------------------------

class ProjectStat(BaseModel):
    project: ProjectOut
    open_tasks: int


class ReviewOut(BaseModel):
    completed_last_7: int
    captured_last_7: int
    inbox_count: int
    open_tasks: int
    stale_tasks: list[TaskOut]
    resurfaced: list[NoteMeta]
    projects: list[ProjectStat]
