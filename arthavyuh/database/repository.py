"""Repository functions for SQLite tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import date

from arthavyuh.core.config import DEFAULT_DB_PATH, resolve_path
from arthavyuh.core.models import Signal
from arthavyuh.database.db import get_connection, initialize_database


def save_symbols(watchlist: list[dict[str, str]], db_path: str | Path = DEFAULT_DB_PATH) -> None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO symbols(symbol, name)
            VALUES(?, ?)
            ON CONFLICT(symbol) DO UPDATE SET name = excluded.name
            """,
            [(item["symbol"], item.get("name")) for item in watchlist],
        )
        connection.commit()


def save_signals(signals: list[Signal], db_path: str | Path = DEFAULT_DB_PATH) -> int:
    if not signals:
        initialize_database(db_path)
        return 0

    initialize_database(db_path)
    rows = []
    for signal in signals:
        data = signal.model_dump(mode="json")
        rows.append(
            (
                data["symbol"],
                data["strategy"],
                data["date"],
                data["status"],
                data["score"],
                data["close"],
                data["entry"],
                data["stop_loss"],
                data["target"],
                data["risk_reward"],
                data["reason"],
                data["invalidation"],
                json.dumps(data["tags"]),
            )
        )

    with get_connection(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO signals(
                symbol, strategy, signal_date, status, score, close, entry,
                stop_loss, target, risk_reward, reason, invalidation, tags
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
    return len(rows)


def fetch_signals_for_date(signal_date: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT symbol, strategy, signal_date AS date, status, score, close,
                   entry, stop_loss, target, risk_reward, reason, invalidation, tags
            FROM signals
            WHERE signal_date = ?
            ORDER BY score DESC, symbol ASC
            """,
            (signal_date,),
        ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item["tags"] or "[]")
        results.append(item)
    return results


def save_daily_report_metadata(
    report_date: str,
    markdown_path: str | Path,
    json_path: str | Path,
    total_symbols_scanned: int,
    total_signals: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO daily_reports(
                report_date, markdown_path, json_path,
                total_symbols_scanned, total_signals
            )
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                report_date,
                str(resolve_path(markdown_path)),
                str(resolve_path(json_path)),
                total_symbols_scanned,
                total_signals,
            ),
        )
        connection.commit()


def save_broker_snapshot(
    broker: str,
    dataset: str,
    payload: Any,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO broker_snapshots(
                broker, dataset, snapshot_date, from_date, to_date, payload
            )
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                broker,
                dataset,
                date.today().isoformat(),
                from_date,
                to_date,
                json.dumps(payload, indent=2, default=str),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
