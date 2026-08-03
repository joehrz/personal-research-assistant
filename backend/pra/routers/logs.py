"""Frontend error reporting and log inspection."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from .. import logging_setup

router = APIRouter(prefix="/api/logs", tags=["logs"])

frontend_log = logging.getLogger("frontend")

LEVELS = {"debug": logging.DEBUG, "info": logging.INFO,
          "warning": logging.WARNING, "error": logging.ERROR}


class ClientLogIn(BaseModel):
    level: str = "error"
    message: str = Field(max_length=4000)
    context: str = Field(default="", max_length=1000)


@router.post("", status_code=204)
def report(body: ClientLogIn):
    level = LEVELS.get(body.level.lower(), logging.ERROR)
    suffix = f" | {body.context}" if body.context else ""
    frontend_log.log(level, "%s%s", body.message, suffix)


@router.get("/tail")
def tail(request: Request, lines: int = Query(default=200, ge=1, le=2000)):
    log_file = request.app.state.log_file
    return {"file": str(log_file), "lines": logging_setup.tail(log_file, lines)}
