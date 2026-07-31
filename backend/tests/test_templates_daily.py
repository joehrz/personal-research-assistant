from datetime import date


def test_default_templates_seeded(client):
    names = {t["name"] for t in client.get("/api/templates").json()}
    assert {"paper-summary", "experiment-log", "meeting", "daily"} <= names


def test_user_edits_to_templates_survive_restart(client, settings):
    path = settings.templates_dir / "meeting.md"
    path.write_text("# My custom meeting\n")

    from fastapi.testclient import TestClient
    from pra.main import create_app
    with TestClient(create_app(settings)) as c2:
        meeting = next(t for t in c2.get("/api/templates").json() if t["name"] == "meeting")
        assert meeting["content"] == "# My custom meeting\n"


def test_templates_not_indexed_as_notes(client):
    assert client.get("/api/notes").json() == []
    hits = client.get("/api/search", params={"q": "hypothesis"}).json()["hits"]
    assert hits == []


def test_daily_note_get_or_create(client):
    a = client.post("/api/notes/daily/today").json()
    today = date.today().isoformat()
    assert a["title"] == today
    assert a["kind"] == "daily"
    assert today in a["content"]  # {{date}} filled from the daily template
    assert "Focus today" in a["content"]

    b = client.post("/api/notes/daily/today").json()
    assert b["id"] == a["id"]  # idempotent — same note, not a duplicate
