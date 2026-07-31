"""Source metadata lookup (DOI via Crossref, arXiv via its Atom API) and
BibTeX export. No AI involved — these are plain metadata registries."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import httpx

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+")
ARXIV_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arxiv\s*:\s*)?(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE
)

USER_AGENT = "personal-research-assistant/0.1 (mailto:local@localhost)"

ATOM = "{http://www.w3.org/2005/Atom}"


def parse_crossref(message: dict) -> dict:
    """Map a Crossref works message to Source fields."""
    title = (message.get("title") or [""])[0]
    authors = []
    for a in message.get("author") or []:
        name = " ".join(x for x in (a.get("given"), a.get("family")) if x)
        if name:
            authors.append(name)
    year = None
    for key in ("published-print", "published-online", "issued"):
        parts = (message.get(key) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            year = int(parts[0][0])
            break
    kind_map = {"journal-article": "paper", "proceedings-article": "paper",
                "book": "book", "monograph": "book", "book-chapter": "book"}
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": (message.get("container-title") or [""])[0],
        "doi": message.get("DOI", ""),
        "url": message.get("URL", ""),
        "kind": kind_map.get(message.get("type", ""), "article"),
    }


def parse_arxiv(xml_text: str) -> dict | None:
    root = ET.fromstring(xml_text)
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        return None
    title = re.sub(r"\s+", " ", (entry.findtext(f"{ATOM}title") or "")).strip()
    if not title or title.lower() == "error":
        return None
    authors = [
        a.findtext(f"{ATOM}name", "").strip()
        for a in entry.findall(f"{ATOM}author")
        if a.findtext(f"{ATOM}name")
    ]
    published = entry.findtext(f"{ATOM}published") or ""
    year = int(published[:4]) if published[:4].isdigit() else None
    arxiv_id = (entry.findtext(f"{ATOM}id") or "").rsplit("/abs/", 1)[-1]
    bare_id = re.sub(r"v\d+$", "", arxiv_id)
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": "arXiv",
        "doi": f"10.48550/arXiv.{bare_id}" if bare_id else "",
        "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
        "kind": "paper",
    }


def fetch_crossref(doi: str) -> dict | None:
    resp = httpx.get(
        f"https://api.crossref.org/works/{doi}",
        headers={"User-Agent": USER_AGENT},
        timeout=15.0, follow_redirects=True,
    )
    if resp.status_code != 200:
        return None
    return parse_crossref(resp.json().get("message") or {})


def fetch_arxiv(arxiv_id: str) -> dict | None:
    resp = httpx.get(
        "https://export.arxiv.org/api/query",
        params={"id_list": arxiv_id},
        headers={"User-Agent": USER_AGENT},
        timeout=15.0, follow_redirects=True,
    )
    if resp.status_code != 200:
        return None
    return parse_arxiv(resp.text)


def lookup(query: str) -> dict | None:
    """Resolve a DOI, arXiv id, or URL containing either, to source metadata."""
    query = query.strip()
    m = DOI_RE.search(query)
    if m and "arxiv" not in m.group(0).lower():
        result = fetch_crossref(m.group(0).rstrip(".,;"))
        if result:
            return result
    m = ARXIV_RE.search(query)
    if m:
        return fetch_arxiv(m.group(1))
    return None


# ---- BibTeX ---------------------------------------------------------------

def _bib_escape(text: str) -> str:
    return text.replace("{", r"\{").replace("}", r"\}").replace("&", r"\&")


def _bib_key(title: str, authors: list[str], year: int | None, taken: set[str]) -> str:
    last = (authors[0].split()[-1] if authors and authors[0].split() else "anon").lower()
    word = next(
        (w.lower() for w in re.findall(r"[A-Za-z]{3,}", title)
         if w.lower() not in {"the", "and", "for", "with", "from"}),
        "work",
    )
    base = re.sub(r"[^a-z0-9]", "", f"{last}{year or ''}{word}") or "source"
    key, n = base, 2
    while key in taken:
        key, n = f"{base}{n}", n + 1
    taken.add(key)
    return key


def to_bibtex(sources: list) -> str:
    """Render Source rows as a BibTeX file."""
    entry_type = {"paper": "article", "article": "misc", "book": "book",
                  "video": "misc", "other": "misc"}
    taken: set[str] = set()
    chunks = []
    for s in sources:
        key = _bib_key(s.title, s.authors or [], s.year, taken)
        fields = [("title", _bib_escape(s.title))]
        if s.authors:
            fields.append(("author", _bib_escape(" and ".join(s.authors))))
        if s.year:
            fields.append(("year", str(s.year)))
        if s.venue:
            fields.append(("journal", _bib_escape(s.venue)))
        if s.doi:
            fields.append(("doi", s.doi))
        if s.url:
            fields.append(("url", s.url))
        body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
        chunks.append(f"@{entry_type.get(s.kind, 'misc')}{{{key},\n{body}\n}}")
    return "\n\n".join(chunks) + ("\n" if chunks else "")
