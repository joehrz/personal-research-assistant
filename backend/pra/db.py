"""Database engine, session management, and full-text search schema.

SQLite is an index and relational store; note *content* lives in Markdown files
in the vault and is mirrored into the FTS table for search.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def make_engine(db_path: Path) -> Engine:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def _ensure_column(conn, table: str, column: str, ddl: str) -> None:
    """Tiny forward-only migration: add a column if an older database lacks it."""
    cols = [row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")]
    if column not in cols:
        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        _ensure_column(conn, "tasks", "duration_min", "INTEGER NOT NULL DEFAULT 60")
        _ensure_column(conn, "tasks", "recurrence", "VARCHAR(40) NOT NULL DEFAULT ''")
        _ensure_column(conn, "sources", "year", "INTEGER")
        _ensure_column(conn, "sources", "venue", "VARCHAR(300) NOT NULL DEFAULT ''")
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    entity_type,
                    entity_id UNINDEXED,
                    title,
                    body,
                    tags,
                    tokenize = 'porter unicode61'
                )
                """
            )
        )


def make_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
