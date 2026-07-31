from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import Link, NoteIndex

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("", response_model=schemas.GraphOut)
def graph(db: Session = Depends(get_db)):
    notes = db.execute(
        select(NoteIndex).where(NoteIndex.inbox.is_(False))
    ).scalars().all()
    ids = {n.id for n in notes}
    edges = db.execute(select(Link).where(Link.kind == "wikilink")).scalars().all()
    return schemas.GraphOut(
        nodes=[schemas.GraphNode(id=n.id, title=n.title, kind=n.kind) for n in notes],
        edges=[
            schemas.GraphEdge(from_id=e.from_id, to_id=e.to_id)
            for e in edges
            if e.from_id in ids and e.to_id in ids
        ],
    )
