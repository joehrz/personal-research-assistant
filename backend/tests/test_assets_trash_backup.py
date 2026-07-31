import io


def test_asset_upload_and_serve(client):
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    r = client.post("/api/assets", files={"file": ("plot.png", io.BytesIO(png), "image/png")})
    assert r.status_code == 201
    body = r.json()
    assert body["is_image"] is True
    assert body["markdown"].startswith("![plot.png](/vault-assets/")

    served = client.get(body["url"])
    assert served.status_code == 200
    assert served.content == png


def test_asset_upload_rejects_empty(client):
    r = client.post("/api/assets", files={"file": ("x.png", io.BytesIO(b""), "image/png")})
    assert r.status_code == 422


def test_trash_restore_roundtrip(client):
    note = client.post("/api/notes", json={"title": "Precious", "content": "do not lose"}).json()
    client.delete(f"/api/notes/{note['id']}")
    assert client.get("/api/notes").json() == []

    trash = client.get("/api/trash").json()
    assert [t["title"] for t in trash] == ["Precious"]

    restored = client.post(f"/api/trash/{trash[0]['name']}/restore").json()
    assert restored["id"] == note["id"]
    assert restored["content"] == "do not lose"
    assert client.get("/api/trash").json() == []
    # restored note is searchable again
    hits = client.get("/api/search", params={"q": "lose"}).json()["hits"]
    assert hits[0]["entity_id"] == note["id"]


def test_trash_purge_single(client):
    note = client.post("/api/notes", json={"title": "Gone", "content": "x"}).json()
    client.delete(f"/api/notes/{note['id']}")
    name = client.get("/api/trash").json()[0]["name"]
    assert client.delete(f"/api/trash/{name}").status_code == 204
    assert client.get("/api/trash").json() == []
    assert client.delete(f"/api/trash/{name}").status_code == 404


def test_backup_creates_git_history(client, settings):
    status = client.get("/api/backup/status").json()
    assert status["git_available"] is True
    assert status["initialized"] is True  # startup backup initialized the repo
    baseline = status["commits"]

    client.post("/api/notes", json={"title": "Backed up", "content": "v1"})
    result = client.post("/api/backup/run").json()
    assert result == {"ok": True, "message": "backed up"}

    status = client.get("/api/backup/status").json()
    assert status["commits"] == baseline + 1
    assert status["last_backup"] is not None

    # no changes -> no new commit
    result = client.post("/api/backup/run").json()
    assert result["message"] == "no changes"


def test_kanban_doing_status(client):
    t = client.post("/api/tasks", json={"text": "run ablations today #thesis"}).json()
    moved = client.patch(f"/api/tasks/{t['id']}", json={"status": "doing"}).json()
    assert moved["status"] == "doing"
    assert moved["completed_at"] is None

    today = client.get("/api/tasks", params={"view": "today"}).json()
    assert [x["id"] for x in today] == [t["id"]]  # doing still shows as open

    done = client.patch(f"/api/tasks/{t['id']}", json={"status": "done"}).json()
    assert done["completed_at"] is not None


def test_graph_endpoint(client):
    a = client.post("/api/notes", json={"title": "Hub", "content": ""}).json()
    client.post("/api/notes", json={"title": "Spoke", "content": "see [[Hub]]"})
    g = client.get("/api/graph").json()
    titles = {n["title"] for n in g["nodes"]}
    assert {"Hub", "Spoke"} <= titles
    assert any(e["to_id"] == a["id"] for e in g["edges"])
