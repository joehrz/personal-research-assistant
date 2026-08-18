from datetime import datetime

from pra.services import calendars

SAMPLE_ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:one@test
DTSTART:20260803T100000
DTEND:20260803T110000
SUMMARY:Lab meeting
LOCATION:Room 204
END:VEVENT
BEGIN:VEVENT
UID:recurring@test
DTSTART:20260804T090000
DTEND:20260804T093000
RRULE:FREQ=WEEKLY;COUNT=10
SUMMARY:Standup
END:VEVENT
BEGIN:VEVENT
UID:allday@test
DTSTART;VALUE=DATE:20260805
DTEND;VALUE=DATE:20260806
SUMMARY:Conference day
END:VEVENT
END:VCALENDAR
"""


def test_parse_events_expands_recurrence_and_all_day():
    events = calendars.parse_events(
        SAMPLE_ICS, datetime(2026, 8, 3), datetime(2026, 8, 17)
    )
    titles = [e["title"] for e in events]
    assert titles.count("Standup") == 2  # Aug 4 and Aug 11
    assert "Lab meeting" in titles
    lab = next(e for e in events if e["title"] == "Lab meeting")
    assert lab["start"] == datetime(2026, 8, 3, 10, 0)
    assert lab["all_day"] is False
    assert lab["location"] == "Room 204"
    allday = next(e for e in events if e["title"] == "Conference day")
    assert allday["all_day"] is True


def test_feed_crud_and_events_endpoint(client, monkeypatch):
    feed = client.post("/api/calendar/feeds", json={
        "name": "Work", "url": "https://example.com/cal.ics", "color": "#f59e0b",
    }).json()
    assert client.get("/api/calendar/feeds").json()[0]["name"] == "Work"

    monkeypatch.setattr(calendars, "fetch_ics", lambda url: SAMPLE_ICS)
    res = client.get("/api/calendar/events", params={
        "start": "2026-08-03T00:00:00", "end": "2026-08-10T00:00:00",
    }).json()
    assert res["errors"] == []
    assert {e["title"] for e in res["events"]} == {"Lab meeting", "Standup", "Conference day"}
    assert all(e["color"] == "#f59e0b" for e in res["events"])

    # disabled feeds are skipped
    client.patch(f"/api/calendar/feeds/{feed['id']}", json={"enabled": False})
    res = client.get("/api/calendar/events", params={
        "start": "2026-08-03T00:00:00", "end": "2026-08-10T00:00:00",
    }).json()
    assert res["events"] == []

    assert client.delete(f"/api/calendar/feeds/{feed['id']}").status_code == 204


def test_broken_feed_reports_error_not_500(client, monkeypatch):
    client.post("/api/calendar/feeds", json={"name": "Bad", "url": "https://x.invalid/c.ics"})

    def boom(url):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(calendars, "fetch_ics", boom)
    res = client.get("/api/calendar/events", params={
        "start": "2026-08-03T00:00:00", "end": "2026-08-10T00:00:00",
    })
    assert res.status_code == 200
    assert res.json()["errors"][0]["feed_name"] == "Bad"


def test_scheduled_view_and_duration(client):
    t = client.post("/api/tasks", json={
        "title": "deep work block",
        "scheduled_at": "2026-08-04T09:00:00",
        "duration_min": 90,
    }).json()
    assert t["duration_min"] == 90

    tasks = client.get("/api/tasks", params={
        "view": "scheduled", "start": "2026-08-03T00:00:00", "end": "2026-08-10T00:00:00",
    }).json()
    assert [x["title"] for x in tasks] == ["deep work block"]

    # completed tasks stay on the calendar
    client.patch(f"/api/tasks/{t['id']}", json={"status": "done"})
    tasks = client.get("/api/tasks", params={
        "view": "scheduled", "start": "2026-08-03T00:00:00", "end": "2026-08-10T00:00:00",
    }).json()
    assert len(tasks) == 1

    # outside the window -> excluded
    tasks = client.get("/api/tasks", params={
        "view": "scheduled", "start": "2026-08-10T00:00:00", "end": "2026-08-17T00:00:00",
    }).json()
    assert tasks == []


def test_reschedule_and_unschedule(client):
    t = client.post("/api/tasks", json={"text": "write methods section"}).json()
    moved = client.patch(f"/api/tasks/{t['id']}", json={
        "scheduled_at": "2026-08-05T14:00:00", "duration_min": 120, "due_date": "2026-08-05",
    }).json()
    assert moved["scheduled_at"] == "2026-08-05T14:00:00"
    cleared = client.patch(f"/api/tasks/{t['id']}", json={"clear_scheduled_at": True}).json()
    assert cleared["scheduled_at"] is None


def test_task_note_link_update_and_clear(client):
    note = client.post("/api/notes", json={"title": "Method ideas", "content": "x"}).json()
    task = client.post("/api/tasks", json={"title": "implement method"}).json()
    linked = client.patch(f"/api/tasks/{task['id']}", json={"note_id": note["id"]}).json()
    assert linked["note_id"] == note["id"]
    cleared = client.patch(f"/api/tasks/{task['id']}", json={"note_id": ""}).json()
    assert cleared["note_id"] is None
