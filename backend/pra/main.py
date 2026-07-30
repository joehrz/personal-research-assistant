"""FastAPI application factory.

Run in development with:

    uvicorn pra.main:create_app --factory --reload --port 8734

The built frontend (frontend/dist) is served at / when present, so the desktop
shell and production mode need only this one server.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings
from .db import init_db, make_engine, make_sessionmaker
from .routers import capture, notes, projects, search, sources, tasks
from .services import vault

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_dirs()

    engine = make_engine(settings.db_path)
    init_db(engine)
    sessionmaker = make_sessionmaker(engine)

    app = FastAPI(title="Personal Research Assistant", version=__version__)
    app.state.settings = settings
    app.state.sessionmaker = sessionmaker

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    with sessionmaker() as session:
        vault.reindex(session, settings)

    for router in (capture, notes, tasks, projects, sources, search):
        app.include_router(router.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": __version__, "data_dir": str(settings.data_dir)}

    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return app
