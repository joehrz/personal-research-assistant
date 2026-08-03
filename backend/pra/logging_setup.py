"""Central logging: everything lands in <data_dir>/logs/pra.log (rotating).

Covers backend startup steps, every HTTP request, unhandled exceptions,
uvicorn's own logs, frontend errors (via POST /api/logs), and the desktop
shell. Set PRA_LOG_LEVEL=DEBUG for maximum detail.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

from .config import Settings

FORMAT = "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"


def setup_logging(settings: Settings) -> Path:
    level = os.environ.get("PRA_LOG_LEVEL", "INFO").upper()
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pra.log"

    root = logging.getLogger()
    root.setLevel(level)
    formatter = logging.Formatter(FORMAT)

    # Replace any handler we installed previously (tests build many apps).
    for handler in list(root.handlers):
        if getattr(handler, "_pra_marker", False):
            root.removeHandler(handler)
            handler.close()

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler._pra_marker = True  # type: ignore[attr-defined]
    root.addHandler(file_handler)

    if not any(
        isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.handlers.RotatingFileHandler)
        for h in root.handlers
    ):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)

    # Route uvicorn's loggers through ours instead of its own config.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv = logging.getLogger(name)
        uv.handlers = []
        uv.propagate = True

    return log_file


def tail(log_file: Path, lines: int) -> list[str]:
    if not log_file.exists():
        return []
    content = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    return content[-lines:]
