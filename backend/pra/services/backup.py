"""Automatic vault backup via a local git repository inside the vault folder.

Every backup is a commit, so the full history of every note is recoverable
with plain git. Fails soft everywhere: no git installed → feature reports
unavailable, app works normally.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import Settings

GITIGNORE = "# managed by personal-research-assistant\n.DS_Store\nThumbs.db\n"


def _git(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(vault), *args],
        capture_output=True, text=True, timeout=60,
    )


def git_available() -> bool:
    try:
        return subprocess.run(["git", "--version"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def is_initialized(settings: Settings) -> bool:
    return (settings.vault_dir / ".git").exists()


def ensure_repo(settings: Settings) -> bool:
    if not git_available():
        return False
    if not is_initialized(settings):
        if _git(settings.vault_dir, "init", "-q").returncode != 0:
            return False
        (settings.vault_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
        _git(settings.vault_dir, "config", "user.name", "vault-backup")
        _git(settings.vault_dir, "config", "user.email", "vault-backup@localhost")
    return True


def run_backup(settings: Settings) -> dict:
    """Commit any vault changes. Returns a status dict; never raises."""
    try:
        if not ensure_repo(settings):
            return {"ok": False, "message": "git not available"}
        _git(settings.vault_dir, "add", "-A")
        if _git(settings.vault_dir, "diff", "--cached", "--quiet").returncode == 0:
            return {"ok": True, "message": "no changes"}
        result = _git(settings.vault_dir, "commit", "-q", "-m", "vault auto-backup")
        if result.returncode != 0:
            return {"ok": False, "message": result.stderr.strip()[:200] or "commit failed"}
        return {"ok": True, "message": "backed up"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": str(exc)[:200]}


def status(settings: Settings) -> dict:
    available = git_available()
    initialized = available and is_initialized(settings)
    last = None
    commits = 0
    if initialized:
        r = _git(settings.vault_dir, "log", "-1", "--format=%cI")
        last = r.stdout.strip() or None
        c = _git(settings.vault_dir, "rev-list", "--count", "HEAD")
        commits = int(c.stdout.strip()) if c.returncode == 0 and c.stdout.strip().isdigit() else 0
    return {
        "git_available": available,
        "initialized": initialized,
        "last_backup": last,
        "commits": commits,
    }
