"""Image/attachment uploads for notes.

Files land in ``vault/assets/<yyyy-mm>/`` and are served back at
``/vault-assets/…`` by the static mount in main.py, so pasted images live
inside the vault and sync/backup with everything else.
"""

from __future__ import annotations

import re
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..config import Settings
from ..deps import get_settings

router = APIRouter(prefix="/api/assets", tags=["assets"])

MAX_BYTES = 25 * 1024 * 1024
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def _safe_name(filename: str) -> str:
    name = re.sub(r"[^\w.\-]", "-", filename or "file").strip("-.") or "file"
    return name[-80:]


@router.post("", status_code=201)
async def upload(file: UploadFile, settings: Settings = Depends(get_settings)):
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File larger than 25 MB")
    if not data:
        raise HTTPException(status_code=422, detail="Empty file")

    name = _safe_name(file.filename or "pasted.png")
    subdir = date.today().strftime("%Y-%m")
    target_dir = settings.assets_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex[:8]}-{name}"
    target.write_bytes(data)

    url = f"/vault-assets/{subdir}/{target.name}"
    is_image = target.suffix.lower() in IMAGE_EXTENSIONS
    markdown = f"![{name}]({url})" if is_image else f"[{name}]({url})"
    return {"url": url, "markdown": markdown, "is_image": is_image}
