"""Application settings.

All state lives under a single data directory so the whole app can be backed up
or synced by copying one folder. Layout:

    <data_dir>/
        pra.db          SQLite database (index + tasks/projects/sources)
        vault/
            inbox/      captured snippets awaiting triage
            notes/      filed notes
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DIR_NAME = ".personal-research-assistant"


@dataclass(frozen=True)
class Settings:
    data_dir: Path

    @property
    def db_path(self) -> Path:
        return self.data_dir / "pra.db"

    @property
    def vault_dir(self) -> Path:
        return self.data_dir / "vault"

    @property
    def inbox_dir(self) -> Path:
        return self.vault_dir / "inbox"

    @property
    def notes_dir(self) -> Path:
        return self.vault_dir / "notes"

    @property
    def templates_dir(self) -> Path:
        return self.vault_dir / "templates"

    @classmethod
    def from_env(cls) -> "Settings":
        raw = os.environ.get("PRA_DATA_DIR")
        data_dir = Path(raw).expanduser() if raw else Path.home() / DEFAULT_DIR_NAME
        return cls(data_dir=data_dir)

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.vault_dir, self.inbox_dir, self.notes_dir,
                  self.templates_dir):
            d.mkdir(parents=True, exist_ok=True)
