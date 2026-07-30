from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..services import search as search_service

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=schemas.SearchOut)
def search(
    q: str = Query(min_length=1),
    types: str | None = None,  # comma-separated: note,task
    limit: int = Query(default=30, le=100),
    db: Session = Depends(get_db),
):
    entity_types = [t.strip() for t in types.split(",") if t.strip()] if types else None
    hits = search_service.search(db, q, entity_types=entity_types, limit=limit)
    return schemas.SearchOut(query=q, hits=[schemas.SearchHit(**h) for h in hits])
