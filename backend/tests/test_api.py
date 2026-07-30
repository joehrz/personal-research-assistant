from datetime import date


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_capture_snippet_with_source(client):
    r = client.post("/api/capture", json={
        "text": "Cool trick for camera calibration",
        "source_url": "https://example.com/post",
        "source_title": "CV blog",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["kind"] == "snippet"
    assert body["note"]["inbox"] is True
    assert body["note"]["source_url"] == "https://example.com/post"

    inbox = client.get("/api/notes", params={"inbox": True}).json()
    assert len(inbox) == 1


def test_capture_code_snippet_detects_language(client):
    r = client.post("/api/capture", json={"text": "```python\nprint('hi')\n```"})
    assert r.json()["note"]["language"] == "python"


def test_capture_todo_creates_task(client):
    r = client.post("/api/capture", json={"text": "todo: email advisor tomorrow p2 #phd"})
    assert r.status_code == 201
    body = r.json()
    assert body["kind"] == "task"
    assert body["task"]["title"] == "email advisor"
    assert body["task"]["priority"] == 2
    assert body["task"]["due_date"] is not None

    projects = client.get("/api/projects").json()
    assert [p["name"] for p in projects] == ["phd"]


def test_task_nl_creation_and_views(client):
    client.post("/api/tasks", json={"text": "write intro section today p1"})
    client.post("/api/tasks", json={"text": "clean dataset in 3 days"})
    client.post("/api/tasks", json={"text": "someday read that book"})

    today = client.get("/api/tasks", params={"view": "today"}).json()
    assert [t["title"] for t in today] == ["write intro section"]

    upcoming = client.get("/api/tasks", params={"view": "upcoming"}).json()
    assert [t["title"] for t in upcoming] == ["clean dataset"]

    inbox = client.get("/api/tasks", params={"view": "inbox"}).json()
    assert [t["title"] for t in inbox] == ["someday read that book"]


def test_task_complete_and_done_view(client):
    task = client.post("/api/tasks", json={"text": "finish experiment"}).json()
    r = client.patch(f"/api/tasks/{task['id']}", json={"status": "done"})
    assert r.json()["completed_at"] is not None
    done = client.get("/api/tasks", params={"view": "done"}).json()
    assert [t["title"] for t in done] == ["finish experiment"]
    assert client.get("/api/tasks", params={"view": "all"}).json() == []


def test_task_clear_due_date(client):
    task = client.post("/api/tasks", json={"text": "review draft friday"}).json()
    assert task["due_date"] is not None
    r = client.patch(f"/api/tasks/{task['id']}", json={"clear_due_date": True})
    assert r.json()["due_date"] is None


def test_note_crud_and_triage(client):
    note = client.post("/api/notes", json={
        "title": "Reading list", "content": "- paper one\n- paper two", "tags": ["ml"],
    }).json()
    assert note["content"].startswith("- paper one")

    got = client.get(f"/api/notes/{note['id']}").json()
    assert got["title"] == "Reading list"

    updated = client.patch(f"/api/notes/{note['id']}", json={"content": "- paper three"}).json()
    assert updated["content"] == "- paper three"

    assert client.delete(f"/api/notes/{note['id']}").status_code == 204
    assert client.get(f"/api/notes/{note['id']}").status_code == 404


def test_search_across_notes_and_tasks(client):
    client.post("/api/capture", json={"text": "Gaussian splatting is fast novel view synthesis"})
    client.post("/api/tasks", json={"text": "implement gaussian splatting demo"})

    hits = client.get("/api/search", params={"q": "gaussian"}).json()["hits"]
    types = {h["entity_type"] for h in hits}
    assert types == {"note", "task"}

    only_notes = client.get("/api/search", params={"q": "gaussian", "types": "note"}).json()["hits"]
    assert {h["entity_type"] for h in only_notes} == {"note"}


def test_search_prefix_matching(client):
    client.post("/api/capture", json={"text": "photogrammetry pipeline notes"})
    hits = client.get("/api/search", params={"q": "photogram"}).json()["hits"]
    assert len(hits) == 1


def test_search_handles_quotes_safely(client):
    r = client.get("/api/search", params={"q": 'weird "quoted* input'})
    assert r.status_code == 200


def test_sources_crud(client):
    src = client.post("/api/sources", json={
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "doi": "10.48550/arXiv.1706.03762",
        "kind": "paper",
    }).json()
    assert src["status"] == "to_read"
    updated = client.patch(f"/api/sources/{src['id']}", json={"status": "reading"}).json()
    assert updated["status"] == "reading"
    assert len(client.get("/api/sources").json()) == 1


def test_edited_file_reindexed_on_restart(client, settings, app):
    note = client.post("/api/notes", json={"title": "Persistent", "content": "v1"}).json()
    path = settings.vault_dir / note["path"]
    text = path.read_text().replace("v1", "v2 external edit")
    path.write_text(text)

    # simulate app restart: new app instance over the same data dir
    from fastapi.testclient import TestClient
    from pra.main import create_app
    with TestClient(create_app(settings)) as c2:
        got = c2.get(f"/api/notes/{note['id']}").json()
        assert "v2 external edit" in got["content"]
        hits = c2.get("/api/search", params={"q": "external"}).json()["hits"]
        assert hits and hits[0]["entity_id"] == note["id"]
