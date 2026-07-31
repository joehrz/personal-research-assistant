from datetime import datetime, timedelta

from pra.models import TimeEntry


def test_start_stop_and_current(client):
    assert client.get("/api/time/current").json() is None

    e = client.post("/api/time/start", json={"label": "deep reading"}).json()
    assert e["label"] == "deep reading"
    assert e["ended_at"] is None

    cur = client.get("/api/time/current").json()
    assert cur["id"] == e["id"]

    stopped = client.post("/api/time/stop").json()
    assert stopped["id"] == e["id"]
    assert stopped["ended_at"] is not None
    assert client.get("/api/time/current").json() is None
    assert client.post("/api/time/stop").json() is None  # idempotent


def test_start_from_task_inherits_label_and_project(client):
    t = client.post("/api/tasks", json={"text": "write intro #thesis"}).json()
    e = client.post("/api/time/start", json={"task_id": t["id"]}).json()
    assert e["label"] == "write intro"
    assert e["project_id"] == t["project_id"]


def test_starting_new_timer_stops_previous(client):
    a = client.post("/api/time/start", json={"label": "a"}).json()
    b = client.post("/api/time/start", json={"label": "b"}).json()
    assert client.get("/api/time/current").json()["id"] == b["id"]
    start = (datetime.now() - timedelta(days=1)).isoformat()
    end = (datetime.now() + timedelta(days=1)).isoformat()
    entries = client.get("/api/time/entries", params={"start": start, "end": end}).json()
    ended = next(x for x in entries if x["id"] == a["id"])
    assert ended["ended_at"] is not None


def test_summary_groups_by_day_and_project(client, app):
    t = client.post("/api/tasks", json={"text": "analysis #thesis"}).json()
    now = datetime.now()
    with app.state.sessionmaker() as session:
        session.add(TimeEntry(label="analysis", project_id=t["project_id"],
                              started_at=now - timedelta(hours=3),
                              ended_at=now - timedelta(hours=2)))
        session.add(TimeEntry(label="misc",
                              started_at=now - timedelta(days=1, hours=2),
                              ended_at=now - timedelta(days=1)))
        session.commit()

    start = (now - timedelta(days=7)).isoformat()
    end = (now + timedelta(days=1)).isoformat()
    s = client.get("/api/time/summary", params={"start": start, "end": end}).json()
    assert s["total_min"] == 180
    assert len(s["by_day"]) == 2
    names = {p["project_name"]: p["minutes"] for p in s["by_project"]}
    assert names["thesis"] == 60
    assert names["No project"] == 120
