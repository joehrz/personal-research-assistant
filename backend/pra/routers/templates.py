from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import schemas
from ..config import Settings
from ..deps import get_settings
from ..services import templates as template_service

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[schemas.TemplateOut])
def list_templates(settings: Settings = Depends(get_settings)):
    return template_service.list_templates(settings)
