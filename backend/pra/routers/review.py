from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..services import review as review_service

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("", response_model=schemas.ReviewOut)
def get_review(db: Session = Depends(get_db)):
    return review_service.build_review(db)
