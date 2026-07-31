from pra.services.wikilinks import extract


def test_extract_targets_and_labels():
    content = "See [[Attention Paper]] and [[Gaussian Splatting|splats]] but not [not a link]."
    assert extract(content) == [
        ("Attention Paper", "Attention Paper"),
        ("Gaussian Splatting", "splats"),
    ]


def test_link_resolves_on_save_and_appears_in_backlinks(client):
    target = client.post("/api/notes", json={"title": "Attention Paper", "content": "…"}).json()
    src = client.post("/api/notes", json={
        "title": "Reading log", "content": "Today I read [[Attention Paper]] — great.",
    }).json()

    assert src["links"] == [{"id": target["id"], "title": "Attention Paper"}]
    backs = client.get(f"/api/notes/{target['id']}/backlinks").json()
    assert [b["title"] for b in backs] == ["Reading log"]


def test_link_resolution_is_case_insensitive(client):
    target = client.post("/api/notes", json={"title": "Deep Learning", "content": ""}).json()
    src = client.post("/api/notes", json={
        "title": "n", "content": "notes on [[deep learning]]",
    }).json()
    assert src["links"][0]["id"] == target["id"]


def test_forward_reference_resolves_after_target_created(client):
    src = client.post("/api/notes", json={
        "title": "Ideas", "content": "expand on [[Future Note]]",
    }).json()
    assert src["links"] == []

    target = client.post("/api/notes", json={"title": "Future Note", "content": ""}).json()
    # re-saving the source re-resolves its links
    src = client.patch(f"/api/notes/{src['id']}", json={
        "content": "expand on [[Future Note]]",
    }).json()
    assert src["links"][0]["id"] == target["id"]


def test_rename_target_keeps_backlink(client):
    target = client.post("/api/notes", json={"title": "Old Name", "content": ""}).json()
    client.post("/api/notes", json={"title": "src", "content": "see [[Old Name]]"})
    client.patch(f"/api/notes/{target['id']}", json={"title": "New Name"})
    backs = client.get(f"/api/notes/{target['id']}/backlinks").json()
    assert [b["title"] for b in backs] == ["src"]


def test_removing_link_from_content_clears_backlink(client):
    target = client.post("/api/notes", json={"title": "T", "content": ""}).json()
    src = client.post("/api/notes", json={"title": "s", "content": "[[T]]"}).json()
    client.patch(f"/api/notes/{src['id']}", json={"content": "no more link"})
    assert client.get(f"/api/notes/{target['id']}/backlinks").json() == []


def test_deleting_source_clears_backlink(client):
    target = client.post("/api/notes", json={"title": "T2", "content": ""}).json()
    src = client.post("/api/notes", json={"title": "s2", "content": "[[T2]]"}).json()
    client.delete(f"/api/notes/{src['id']}")
    assert client.get(f"/api/notes/{target['id']}/backlinks").json() == []


def test_reindex_resolves_cross_file_links(client, settings):
    # files written externally, in an order where the link target sorts later
    settings.ensure_dirs()
    (settings.notes_dir / "a-source.md").write_text(
        "---\ntitle: A Source\n---\n\nlinks to [[Z Target]]\n"
    )
    (settings.notes_dir / "z-target.md").write_text("---\ntitle: Z Target\n---\n\nx\n")

    from fastapi.testclient import TestClient
    from pra.main import create_app
    with TestClient(create_app(settings)) as c2:
        notes = c2.get("/api/notes").json()
        target_id = next(n["id"] for n in notes if n["title"] == "Z Target")
        backs = c2.get(f"/api/notes/{target_id}/backlinks").json()
        assert [b["title"] for b in backs] == ["A Source"]
