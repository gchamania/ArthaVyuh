import sqlite3
from pathlib import Path

from arthavyuh.database.db import initialize_database


def test_database_initialization(tmp_path: Path) -> None:
    db_path = initialize_database(tmp_path / "arthavyuh.db")

    assert db_path.exists()
    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "signals" in tables
    assert "trades" in tables
    assert "journal_entries" in tables
