"""FastAPI application factory.

Run in development with:

    uvicorn pra.main:create_app --factory --reload --port 8734

The built frontend (frontend/dist) is served at / when present, so the desktop
shell and production mode need only this one server. All activity is logged to
<data_dir>/logs/pra.log (see logging_setup; PRA_LOG_LEVEL=DEBUG for more).
"""

from __future__ import annotations

import logging
import os
import threading
import time as time_module
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings
from .db import init_db, make_engine, make_sessionmaker
from .logging_setup import setup_logging
from .routers import (
    assets, backup, calendar, capture, graph, logs, notes, projects, review,
    search, sources, tasks, templates, time, trash,
)
from .services import backup as backup_service
from .services import templates as template_service
from .services import vault

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

log = logging.getLogger("pra.app")
http_log = logging.getLogger("pra.http")

# Requests too chatty to log individually.
QUIET_PATHS = ("/assets/", "/vault-assets/", "/api/logs", "/api/time/current")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_dirs()
    log_file = setup_logging(settings)

    log.info("=== starting Personal Research Assistant v%s ===", __version__)
    log.info("data dir: %s | log file: %s", settings.data_dir, log_file)

    engine = make_engine(settings.db_path)
    init_db(engine)
    log.info("database ready: %s", settings.db_path)
    sessionmaker = make_sessionmaker(engine)

    app = FastAPI(title="Personal Research Assistant", version=__version__)
    app.state.settings = settings
    app.state.sessionmaker = sessionmaker
    app.state.log_file = log_file

    # Dev frontend + the browser clipper extension (server binds 127.0.0.1 only).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_origin_regex=r"(chrome|moz)-extension://.*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time_module.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("UNHANDLED ERROR: %s %s", request.method, request.url.path)
            raise
        if not any(request.url.path.startswith(p) for p in QUIET_PATHS):
            http_log.info(
                "%s %s -> %s (%.0f ms)",
                request.method, request.url.path, response.status_code,
                (time_module.perf_counter() - started) * 1000,
            )
        return response

    template_service.seed_defaults(settings)
    log.info("templates seeded/checked")
    with sessionmaker() as session:
        count = vault.reindex(session, settings)
    log.info("vault reindexed: %d notes", count)
    purged = vault.purge_trash(settings, older_than_days=vault.TRASH_RETENTION_DAYS)
    log.info("trash purge: %d expired item(s) removed", purged)
    backup_result = backup_service.run_backup(settings)
    log.info("startup vault backup: %s", backup_result["message"])

    # Periodic auto-backup while the app stays running (0 disables).
    interval_min = int(os.environ.get("PRA_BACKUP_INTERVAL_MIN", "240"))
    if interval_min > 0:
        def _backup_loop() -> None:
            while True:
                time_module.sleep(interval_min * 60)
                result = backup_service.run_backup(settings)
                log.info("periodic vault backup: %s", result["message"])

        threading.Thread(target=_backup_loop, daemon=True, name="backup-loop").start()
        log.info("periodic vault backup every %d min", interval_min)

    for router in (capture, notes, tasks, projects, sources, search, calendar, review,
                   templates, time, assets, trash, backup, graph, logs):
        app.include_router(router.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": __version__, "data_dir": str(settings.data_dir)}

    # NOTE: must not be "/assets" — that would shadow the built frontend's
    # /assets/*.js bundles served by the dist mount below.
    app.mount("/vault-assets", StaticFiles(directory=settings.assets_dir), name="vault-assets")

    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
        log.info("serving built frontend from %s", FRONTEND_DIST)
    else:
        log.warning("frontend/dist not found — API only (run: cd frontend && npm run build)")

    log.info("startup complete — %d routes", len(app.routes))
    return app
