"""SQLAlchemy models.

NoteIndex rows mirror Markdown files in the vault (the file is the source of
truth); Task, Project, Source, and Link live only in SQLite.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    color: Mapped[str] = mapped_column(String(20), default="#6366f1")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="todo")  # todo | done
    priority: Mapped[int] = mapped_column(Integer, default=4)  # 1 (highest) .. 4 (none)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_min: Mapped[int] = mapped_column(Integer, default=60)
    # canonical recurrence: "" | daily | weekdays | weekly:<0-6> | monthly:<1-31>
    # | every:<n>:days | every:<n>:weeks
    recurrence: Mapped[str] = mapped_column(String(40), default="")
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True
    )
    note_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # spawned from note
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[list] = mapped_column(JSON, default=list)
    url: Mapped[str] = mapped_column(String(1000), default="")
    doi: Mapped[str] = mapped_column(String(200), default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str] = mapped_column(String(300), default="")  # journal / conference
    kind: Mapped[str] = mapped_column(String(20), default="article")  # paper|article|book|video|other
    status: Mapped[str] = mapped_column(String(20), default="to_read")  # to_read|reading|read
    notes: Mapped[str] = mapped_column(Text, default="")
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class NoteIndex(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    path: Mapped[str] = mapped_column(String(1000), unique=True)  # relative to vault dir
    title: Mapped[str] = mapped_column(String(500), default="")
    kind: Mapped[str] = mapped_column(String(20), default="note")  # note | snippet
    inbox: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    language: Mapped[str] = mapped_column(String(40), default="")  # code snippet language
    source_url: Mapped[str] = mapped_column(String(1000), default="")
    source_title: Mapped[str] = mapped_column(String(500), default="")
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


def now_local() -> datetime:
    """Local wall-clock time, like Task.scheduled_at — day boundaries in
    time-tracking analytics must match the user's day, not UTC's."""
    return datetime.now().replace(microsecond=0)


class TimeEntry(Base):
    """A tracked focus session; at most one entry runs (ended_at IS NULL)."""

    __tablename__ = "time_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    label: Mapped[str] = mapped_column(String(300), default="")
    task_id: Mapped[str | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CalendarFeed(Base):
    """A subscribed iCalendar (ICS) URL — e.g. a Google Calendar secret
    address — shown read-only alongside scheduled tasks."""

    __tablename__ = "calendar_feeds"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2000))
    color: Mapped[str] = mapped_column(String(20), default="#22c55e")
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Link(Base):
    """Generic association between any two entities (note, task, source, project)."""

    __tablename__ = "links"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    from_type: Mapped[str] = mapped_column(String(20))
    from_id: Mapped[str] = mapped_column(String(32))
    to_type: Mapped[str] = mapped_column(String(20))
    to_id: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(40), default="related")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
