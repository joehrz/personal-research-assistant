"""Natural-language task parsing.

Turns entries like

    review CV paper draft friday 2pm #thesis p1 @deep-work

into structured fields:

    title="review CV paper draft", due_date=<next friday>,
    scheduled_at=<next friday 14:00>, priority=1, project="thesis",
    tags=["deep-work"]

Rules:
- ``#word``            -> project name
- ``@word``            -> tag (repeatable)
- ``p1``..``p4``       -> priority (1 highest; default 4 = none)
- date words           -> due_date: today, tomorrow, weekday names ("fri",
                          "friday", "next friday"), "next week", "in N days",
                          ISO dates (2026-07-30), and "jul 30" / "july 30"
- time                 -> scheduled_at: "2pm", "2:30pm", "14:30", optionally
                          prefixed with "at". A time implies scheduling on the
                          parsed date (or today when no date was given).
All matched tokens are removed from the title.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_PRIORITY_RE = re.compile(r"(?:^|\s)p([1-4])(?=\s|$)", re.IGNORECASE)
_PROJECT_RE = re.compile(r"(?:^|\s)#([\w][\w/-]*)", re.UNICODE)
_TAG_RE = re.compile(r"(?:^|\s)@([\w][\w/-]*)", re.UNICODE)
_ISO_DATE_RE = re.compile(r"(?:^|\s)(\d{4})-(\d{2})-(\d{2})(?=\s|$)")
_MONTH_DAY_RE = re.compile(
    r"(?:^|\s)(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?=\s|$)", re.IGNORECASE
)
_IN_N_DAYS_RE = re.compile(r"(?:^|\s)in\s+(\d{1,3})\s+days?(?=\s|$)", re.IGNORECASE)
_NEXT_WEEK_RE = re.compile(r"(?:^|\s)next\s+week(?=\s|$)", re.IGNORECASE)
_RELATIVE_RE = re.compile(r"(?:^|\s)(today|tonight|tomorrow|tmr)(?=\s|$)", re.IGNORECASE)
_WEEKDAY_RE = re.compile(
    r"(?:^|\s)(next\s+|this\s+)?(" + "|".join(WEEKDAYS) + r")(?=\s|$)", re.IGNORECASE
)
_TIME_RE = re.compile(
    r"(?:^|\s)(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)(?=\s|$)"
    r"|(?:^|\s)(?:at\s+)?(\d{1,2}):(\d{2})(?=\s|$)",
    re.IGNORECASE,
)


@dataclass
class ParsedTask:
    title: str
    due_date: date | None = None
    scheduled_at: datetime | None = None
    priority: int = 4
    project: str | None = None
    tags: list[str] = field(default_factory=list)
    recurrence: str = ""


def _cut(text: str, start: int, end: int) -> str:
    return text[:start] + " " + text[end:]


def _next_weekday(today: date, weekday: int, force_next_week: bool) -> date:
    delta = (weekday - today.weekday()) % 7
    if delta == 0:
        delta = 7 if force_next_week else 0
    elif force_next_week and delta < 7:
        # "next friday" said on a monday still means the coming friday in
        # common usage; only bump a week when the weekday is today.
        pass
    return today + timedelta(days=delta)


def parse(text: str, now: datetime | None = None) -> ParsedTask:
    from . import recurrence as recurrence_service  # local import: avoids cycle

    now = now or datetime.now()
    today = now.date()
    working = text.strip()

    # Recurrence first, so "every monday" isn't consumed as a plain date.
    recurrence, working = recurrence_service.extract(working)

    priority = 4
    m = _PRIORITY_RE.search(working)
    if m:
        priority = int(m.group(1))
        working = _cut(working, m.start(), m.end())

    project: str | None = None
    m = _PROJECT_RE.search(working)
    if m:
        project = m.group(1)
        working = _cut(working, m.start(), m.end())

    tags: list[str] = []
    while (m := _TAG_RE.search(working)) is not None:
        tags.append(m.group(1))
        working = _cut(working, m.start(), m.end())

    due: date | None = None

    m = _ISO_DATE_RE.search(working)
    if m:
        try:
            due = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            working = _cut(working, m.start(), m.end())
        except ValueError:
            pass

    if due is None:
        m = _MONTH_DAY_RE.search(working)
        if m:
            month, day = MONTHS[m.group(1).lower()], int(m.group(2))
            try:
                candidate = date(today.year, month, day)
                if candidate < today:
                    candidate = date(today.year + 1, month, day)
                due = candidate
                working = _cut(working, m.start(), m.end())
            except ValueError:
                pass

    if due is None:
        m = _IN_N_DAYS_RE.search(working)
        if m:
            due = today + timedelta(days=int(m.group(1)))
            working = _cut(working, m.start(), m.end())

    if due is None:
        m = _NEXT_WEEK_RE.search(working)
        if m:
            due = today + timedelta(days=(7 - today.weekday()))  # next Monday
            working = _cut(working, m.start(), m.end())

    if due is None:
        m = _RELATIVE_RE.search(working)
        if m:
            word = m.group(1).lower()
            due = today if word in ("today", "tonight") else today + timedelta(days=1)
            working = _cut(working, m.start(), m.end())

    if due is None:
        m = _WEEKDAY_RE.search(working)
        if m:
            force_next = bool(m.group(1) and "next" in m.group(1).lower())
            due = _next_weekday(today, WEEKDAYS[m.group(2).lower()], force_next)
            working = _cut(working, m.start(), m.end())

    had_explicit_date = due is not None

    scheduled: datetime | None = None
    m = _TIME_RE.search(working)
    if m:
        if m.group(1) is not None:  # am/pm form
            hour = int(m.group(1)) % 12
            if m.group(3).lower() == "pm":
                hour += 12
            minute = int(m.group(2) or 0)
        else:  # 24h form
            hour = int(m.group(4))
            minute = int(m.group(5))
        if hour < 24 and minute < 60:
            base = due or today
            scheduled = datetime.combine(base, time(hour, minute))
            if due is None and scheduled <= now:
                scheduled += timedelta(days=1)
            working = _cut(working, m.start(), m.end())

    if scheduled is not None and due is None:
        due = scheduled.date()

    if recurrence:
        recurrence = recurrence_service.anchor(recurrence, due)
        # "every friday 4pm" with no explicit date: the recurrence anchor
        # decides the first occurrence, overriding the time-implied today.
        if not had_explicit_date:
            due = recurrence_service.first_due(recurrence, today)
            if scheduled is not None:
                scheduled = datetime.combine(due, scheduled.time())

    title = re.sub(r"\s+", " ", working).strip()
    return ParsedTask(
        title=title,
        due_date=due,
        scheduled_at=scheduled,
        priority=priority,
        project=project,
        tags=tags,
        recurrence=recurrence,
    )
