"""FastAPI dependencies pulling app-scoped state (settings, sessionmaker)."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from .config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Generator[Session, None, None]:
    session: Session = request.app.state.sessionmaker()
    try:
        yield session
    finally:
        session.close()
