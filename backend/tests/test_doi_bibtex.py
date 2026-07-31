from types import SimpleNamespace

from pra.services import doi

CROSSREF_MESSAGE = {
    "title": ["Attention Is All You Need"],
    "author": [
        {"given": "Ashish", "family": "Vaswani"},
        {"given": "Noam", "family": "Shazeer"},
    ],
    "issued": {"date-parts": [[2017, 6]]},
    "container-title": ["Advances in Neural Information Processing Systems"],
    "DOI": "10.5555/3295222",
    "URL": "https://doi.org/10.5555/3295222",
    "type": "proceedings-article",
}

ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2308.04079v1</id>
    <published>2023-08-08T00:00:00Z</published>
    <title>3D Gaussian Splatting for
      Real-Time Radiance Field Rendering</title>
    <author><name>Bernhard Kerbl</name></author>
    <author><name>Georgios Kopanas</name></author>
  </entry>
</feed>
"""


def test_parse_crossref():
    r = doi.parse_crossref(CROSSREF_MESSAGE)
    assert r["title"] == "Attention Is All You Need"
    assert r["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
    assert r["year"] == 2017
    assert r["venue"].startswith("Advances")
    assert r["kind"] == "paper"


def test_parse_arxiv_normalizes_whitespace_and_id():
    r = doi.parse_arxiv(ARXIV_XML)
    assert r["title"] == "3D Gaussian Splatting for Real-Time Radiance Field Rendering"
    assert r["authors"] == ["Bernhard Kerbl", "Georgios Kopanas"]
    assert r["year"] == 2023
    assert r["doi"] == "10.48550/arXiv.2308.04079"
    assert r["url"] == "https://arxiv.org/abs/2308.04079v1"


def test_lookup_routes_to_the_right_registry(monkeypatch):
    monkeypatch.setattr(doi, "fetch_crossref", lambda d: {"via": "crossref", "doi": d})
    monkeypatch.setattr(doi, "fetch_arxiv", lambda a: {"via": "arxiv", "id": a})

    assert doi.lookup("https://doi.org/10.1145/3592433")["via"] == "crossref"
    assert doi.lookup("arXiv:2308.04079v2")["id"] == "2308.04079"
    assert doi.lookup("https://arxiv.org/abs/2308.04079")["id"] == "2308.04079"
    assert doi.lookup("no identifiers here") is None


def test_bibtex_output_and_key_dedup():
    mk = lambda **kw: SimpleNamespace(**{
        "title": "T", "authors": [], "year": None, "venue": "", "doi": "",
        "url": "", "kind": "paper", **kw})
    sources = [
        mk(title="Splatting Methods", authors=["Bernhard Kerbl"], year=2023,
           venue="SIGGRAPH", doi="10.1145/3592433"),
        mk(title="Splatting Again", authors=["Bernhard Kerbl"], year=2023),
        mk(title="A Book about Plants {and} Cameras", authors=["Ada Lovelace"],
           year=1843, kind="book"),
    ]
    bib = doi.to_bibtex(sources)
    assert "@article{kerbl2023splatting," in bib
    assert "@article{kerbl2023splatting2," in bib  # key collision -> suffix
    assert "@book{lovelace1843book," in bib
    assert r"\{and\}" in bib  # braces escaped
    assert "doi = {10.1145/3592433}" in bib


def test_lookup_endpoint_404_when_unresolvable(client):
    r = client.post("/api/sources/lookup", json={"query": "just words"})
    assert r.status_code == 404


def test_export_bib_endpoint(client):
    client.post("/api/sources", json={
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani"], "year": 2017, "kind": "paper",
        "venue": "NeurIPS",
    })
    r = client.get("/api/sources/export.bib")
    assert r.status_code == 200
    assert "@article{vaswani2017attention," in r.text
    assert "journal = {NeurIPS}" in r.text
