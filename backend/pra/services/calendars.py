"""Read-only external calendars via iCalendar (ICS) feed subscriptions.

Google Calendar, Outlook, and most other calendars expose a private ICS URL
("secret address in iCal format"), which gives us read-only sync with zero
OAuth setup. Feeds are fetched with a short in-memory cache and recurring
events are expanded with `recurring-ical-events`.
"""

from __future__ import annotations

import time
from datetime import date, datetime

import httpx
import recurring_ical_events
from icalendar import Calendar

FETCH_TTL_SECONDS = 300
_cache: dict[str, tuple[float, str]] = {}


def fetch_ics(url: str, ttl: float = FETCH_TTL_SECONDS) -> str:
    hit = _cache.get(url)
    now = time.monotonic()
    if hit and now - hit[0] < ttl:
        return hit[1]
    resp = httpx.get(url, timeout=10.0, follow_redirects=True)
    resp.raise_for_status()
    _cache[url] = (now, resp.text)
    return resp.text


def _normalize(value) -> tuple[datetime, bool]:
    """Return (naive local datetime, is_all_day)."""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone().replace(tzinfo=None)
        return value, False
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time()), True
    raise ValueError(f"Unsupported ICS date value: {value!r}")


def parse_events(ics_text: str, start: datetime, end: datetime) -> list[dict]:
    """Expand events (including recurrences) overlapping [start, end)."""
    cal = Calendar.from_ical(ics_text)
    out: list[dict] = []
    for ev in recurring_ical_events.of(cal).between(start, end):
        dtstart, all_day = _normalize(ev.get("DTSTART").dt)
        dtend_prop = ev.get("DTEND") or ev.get("DTSTART")
        dtend, _ = _normalize(dtend_prop.dt)
        out.append(
            {
                "title": str(ev.get("SUMMARY", "Untitled")),
                "start": dtstart,
                "end": dtend,
                "all_day": all_day,
                "location": str(ev.get("LOCATION", "")),
            }
        )
    out.sort(key=lambda e: e["start"])
    return out
