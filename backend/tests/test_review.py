from datetime import date, datetime, timedelta

from pra.models import NoteIndex, Task


def test_review_empty(client):
    r = client.get("/api/review").json()
    assert r["completed_last_7"] == 0
    assert r["stale_tasks"] == []
    assert r["resurfaced"] == []


def test_review_aggregates(client, app):
    client.post("/api/capture", json={"text": "an inbox snippet"})
    client.post("/api/tasks", json={"text": "fresh task today #thesis"})
    done = client.post("/api/tasks", json={"title": "finished thing"}).json()
    client.patch(f"/api/tasks/{done['id']}", json={"status": "done"})

    # backdate directly: an overdue task and a dateless task from a month ago
    with app.state.sessionmaker() as session:
        session.add(Task(title="very overdue", due_date=date.today() - timedelta(days=10)))
        session.add(Task(title="forgotten", created_at=datetime.now() - timedelta(days=30)))
        session.commit()

    r = client.get("/api/review").json()
    assert r["completed_last_7"] == 1
    assert r["captured_last_7"] == 1
    assert r["inbox_count"] == 1
    stale_titles = {t["title"] for t in r["stale_tasks"]}
    assert stale_titles == {"very overdue", "forgotten"}
    assert "fresh task today" not in stale_titles
    assert r["projects"][0]["project"]["name"] == "thesis"
    assert r["projects"][0]["open_tasks"] == 1


def test_review_resurfaces_old_notes_only(client, app):
    note = client.post("/api/notes", json={"title": "Ancient wisdom", "content": "x"}).json()
    client.post("/api/notes", json={"title": "Fresh note", "content": "y"})

    with app.state.sessionmaker() as session:
        old = session.get(NoteIndex, note["id"])
        old.modified_at = datetime.now() - timedelta(days=90)
        session.commit()

    r = client.get("/api/review").json()
    assert [n["title"] for n in r["resurfaced"]] == ["Ancient wisdom"]

    # "mark reviewed" = empty PATCH bumps modified_at, so it stops resurfacing
    client.patch(f"/api/notes/{note['id']}", json={})
    r = client.get("/api/review").json()
    assert r["resurfaced"] == []
