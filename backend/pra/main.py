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
from .routers import (
    assets, backup, calendar, capture, graph, notes, projects, review, search,
    sources, tasks, templates, time, trash,
)
from .services import backup as backup_service
from .services import templates as template_service
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

    # Dev frontend + the browser clipper extension (server binds 127.0.0.1 only).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_origin_regex=r"(chrome|moz)-extension://.*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    template_service.seed_defaults(settings)
    with sessionmaker() as session:
        vault.reindex(session, settings)
    vault.purge_trash(settings, older_than_days=vault.TRASH_RETENTION_DAYS)
    backup_service.run_backup(settings)  # snapshot the vault on every startup

    for router in (capture, notes, tasks, projects, sources, search, calendar, review,
                   templates, time, assets, trash, backup, graph):
        app.include_router(router.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": __version__, "data_dir": str(settings.data_dir)}

    # NOTE: must not be "/assets" — that would shadow the built frontend's
    # /assets/*.js bundles served by the dist mount below.
    app.mount("/vault-assets", StaticFiles(directory=settings.assets_dir), name="vault-assets")

    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return app
