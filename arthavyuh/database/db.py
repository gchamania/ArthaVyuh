"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from arthavyuh.core.config import DEFAULT_DB_PATH, PROJECT_ROOT, resolve_path

SCHEMA_PATH = PROJECT_ROOT / "arthavyuh" / "database" / "schema.sql"


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    resolved = resolve_path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    resolved = resolve_path(db_path)
    with get_connection(resolved) as connection:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)
        connection.commit()
    return resolved
