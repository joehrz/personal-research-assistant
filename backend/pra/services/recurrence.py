"""Recurring tasks: parse natural-language recurrence and compute occurrences.

Canonical forms stored on ``Task.recurrence``:

    daily            every day
    weekdays         Monday–Friday
    weekly:<0-6>     weekly on a weekday (0 = Monday)
    monthly:<1-31>   monthly on a day (clamped to short months)
    every:<n>:days   every n days
    every:<n>:weeks  every n weeks

Completing a recurring task spawns the next occurrence; see the tasks router.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

from .taskparse import WEEKDAYS

_EVERY_N_RE = re.compile(
    r"(?:^|\s)every\s+(\d{1,2})\s+(day|week)s?(?=\s|$)", re.IGNORECASE
)
_EVERY_WEEKDAY_RE = re.compile(
    r"(?:^|\s)every\s+(" + "|".join(WEEKDAYS) + r")(?=\s|$)", re.IGNORECASE
)
_KEYWORD_RES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?:^|\s)(every\s+day|daily)(?=\s|$)", re.IGNORECASE), "daily"),
    (re.compile(r"(?:^|\s)(every\s+weekday|weekdays)(?=\s|$)", re.IGNORECASE), "weekdays"),
    (re.compile(r"(?:^|\s)(every\s+week|weekly)(?=\s|$)", re.IGNORECASE), "weekly"),
    (re.compile(r"(?:^|\s)(every\s+month|monthly)(?=\s|$)", re.IGNORECASE), "monthly"),
]


def extract(text: str) -> tuple[str, str]:
    """Pull a recurrence phrase out of task text.

    Returns (canonical_recurrence, remaining_text); recurrence is "" if none.
    ``weekly``/``monthly`` without an anchor day are anchored later, to the
    task's first due date (see :func:`anchor`).
    """
    m = _EVERY_N_RE.search(text)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        canonical = "daily" if (n == 1 and unit == "day") else f"every:{n}:{unit}s"
        return canonical, (text[: m.start()] + " " + text[m.end():])

    m = _EVERY_WEEKDAY_RE.search(text)
    if m:
        weekday = WEEKDAYS[m.group(1).lower()]
        return f"weekly:{weekday}", (text[: m.start()] + " " + text[m.end():])

    for pattern, canonical in _KEYWORD_RES:
        m = pattern.search(text)
        if m:
            return canonical, (text[: m.start()] + " " + text[m.end():])

    return "", text


def anchor(recurrence: str, due: date | None) -> str:
    """Anchor bare weekly/monthly recurrences to the task's due date."""
    if recurrence == "weekly":
        return f"weekly:{(due or date.today()).weekday()}"
    if recurrence == "monthly":
        return f"monthly:{(due or date.today()).day}"
    return recurrence


def first_due(recurrence: str, today: date | None = None) -> date:
    """A sensible initial due date when the task text had no explicit date."""
    today = today or date.today()
    return next_occurrence(recurrence, today - timedelta(days=1))


def next_occurrence(recurrence: str, after: date) -> date:
    """The first occurrence strictly after ``after``."""
    if recurrence == "daily":
        return after + timedelta(days=1)

    if recurrence == "weekdays":
        nxt = after + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        return nxt

    if recurrence.startswith("weekly:"):
        weekday = int(recurrence.split(":")[1])
        delta = (weekday - after.weekday() - 1) % 7 + 1
        return after + timedelta(days=delta)

    if recurrence.startswith("monthly:"):
        day = int(recurrence.split(":")[1])
        year, month = after.year, after.month
        for _ in range(2):  # this month if still ahead, else next month
            clamped = min(day, calendar.monthrange(year, month)[1])
            candidate = date(year, month, clamped)
            if candidate > after:
                return candidate
            month += 1
            if month > 12:
                month, year = 1, year + 1
        raise AssertionError("unreachable")

    if recurrence.startswith("every:"):
        _, n, unit = recurrence.split(":")
        step = timedelta(days=int(n)) if unit == "days" else timedelta(weeks=int(n))
        return after + step

    raise ValueError(f"Unknown recurrence: {recurrence!r}")
