from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import Source
from ..services import doi as doi_service

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.post("/lookup", response_model=schemas.SourceLookupOut)
def lookup(body: schemas.SourceLookupIn):
    try:
        result = doi_service.lookup(body.query)
    except Exception as exc:  # network failures surface as a clean 502
        raise HTTPException(status_code=502, detail=f"Lookup failed: {exc}") from exc
    if result is None:
        raise HTTPException(status_code=404, detail="No DOI or arXiv id found in query")
    return result


@router.get("/export.bib", response_class=PlainTextResponse)
def export_bibtex(db: Session = Depends(get_db)):
    sources = db.execute(select(Source).order_by(Source.created_at)).scalars().all()
    return PlainTextResponse(
        doi_service.to_bibtex(sources),
        headers={"Content-Disposition": 'attachment; filename="sources.bib"'},
    )


@router.get("", response_model=list[schemas.SourceOut])
def list_sources(
    status: str | None = None,
    kind: str | None = None,
    project_id: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Source).order_by(Source.created_at.desc())
    if status:
        stmt = stmt.where(Source.status == status)
    if kind:
        stmt = stmt.where(Source.kind == kind)
    if project_id:
        stmt = stmt.where(Source.project_id == project_id)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=schemas.SourceOut, status_code=201)
def create_source(body: schemas.SourceCreate, db: Session = Depends(get_db)):
    source = Source(**body.model_dump())
    db.add(source)
    db.commit()
    return source


@router.patch("/{source_id}", response_model=schemas.SourceOut)
def update_source(source_id: str, body: schemas.SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(source, key, value)
    db.commit()
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: str, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
