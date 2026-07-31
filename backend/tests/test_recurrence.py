from datetime import date, datetime

from pra.services.recurrence import extract, next_occurrence
from pra.services.taskparse import parse

NOW = datetime(2026, 7, 29, 10, 0)  # a Wednesday


def test_extract_forms():
    assert extract("water plants every day")[0] == "daily"
    assert extract("standup daily")[0] == "daily"
    assert extract("gym every weekday")[0] == "weekdays"
    assert extract("review every monday")[0] == "weekly:0"
    assert extract("backup every 2 weeks")[0] == "every:2:weeks"
    assert extract("stretch every 3 days")[0] == "every:3:days"
    assert extract("rent monthly")[0] == "monthly"
    assert extract("nothing recurring here")[0] == ""


def test_next_occurrence():
    wed = date(2026, 7, 29)
    assert next_occurrence("daily", wed) == date(2026, 7, 30)
    assert next_occurrence("weekdays", date(2026, 7, 31)) == date(2026, 8, 3)  # Fri -> Mon
    assert next_occurrence("weekly:0", wed) == date(2026, 8, 3)  # next Monday
    assert next_occurrence("weekly:2", wed) == date(2026, 8, 5)  # Wed -> next Wed
    assert next_occurrence("every:2:weeks", wed) == date(2026, 8, 12)
    assert next_occurrence("monthly:31", date(2026, 8, 31)) == date(2026, 9, 30)  # clamped


def test_parse_recurrence_sets_due():
    p = parse("weekly report every friday 4pm #thesis", now=NOW)
    assert p.recurrence == "weekly:4"
    assert p.title == "weekly report"
    assert p.due_date == date(2026, 7, 31)  # coming Friday
    assert p.scheduled_at == datetime(2026, 7, 31, 16, 0)
    assert p.project == "thesis"


def test_parse_bare_weekly_anchors_to_explicit_date():
    p = parse("water plants weekly saturday", now=NOW)
    assert p.recurrence == "weekly:5"
    assert p.due_date == date(2026, 8, 1)


def test_completing_recurring_task_spawns_next(client):
    t = client.post("/api/tasks", json={"text": "lab log every weekday 9am"}).json()
    assert t["recurrence"] == "weekdays"

    client.patch(f"/api/tasks/{t['id']}", json={"status": "done"})

    todos = client.get("/api/tasks", params={"view": "all"}).json()
    assert len(todos) == 1
    nxt = todos[0]
    assert nxt["id"] != t["id"]
    assert nxt["title"] == "lab log"
    assert nxt["recurrence"] == "weekdays"
    assert nxt["due_date"] > t["due_date"]
    assert nxt["scheduled_at"].endswith("09:00:00")

    done = client.get("/api/tasks", params={"view": "done"}).json()
    assert len(done) == 1  # completed occurrence kept as history


def test_uncompleting_does_not_spawn(client):
    t = client.post("/api/tasks", json={"text": "journal daily"}).json()
    client.patch(f"/api/tasks/{t['id']}", json={"status": "done"})
    client.patch(f"/api/tasks/{t['id']}", json={"status": "todo"})
    todos = client.get("/api/tasks", params={"view": "all"}).json()
    assert len(todos) == 2  # original back + one spawned; no extras


def test_clear_recurrence(client):
    t = client.post("/api/tasks", json={"text": "sync notes weekly"}).json()
    cleared = client.patch(f"/api/tasks/{t['id']}", json={"recurrence": ""}).json()
    assert cleared["recurrence"] == ""


def test_notes_filter_by_source(client):
    src = client.post("/api/sources", json={"title": "Splatting paper", "kind": "paper"}).json()
    linked = client.post("/api/notes", json={"title": "quote", "source_id": src["id"]}).json()
    client.post("/api/notes", json={"title": "unrelated"})
    notes = client.get("/api/notes", params={"source_id": src["id"]}).json()
    assert [n["id"] for n in notes] == [linked["id"]]
