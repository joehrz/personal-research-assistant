from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import schemas
from ..config import Settings
from ..deps import get_settings
from ..services import backup as backup_service

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/status", response_model=schemas.BackupStatus)
def status(settings: Settings = Depends(get_settings)):
    return backup_service.status(settings)


@router.post("/run", response_model=schemas.BackupResult)
def run(settings: Settings = Depends(get_settings)):
    return backup_service.run_backup(settings)
