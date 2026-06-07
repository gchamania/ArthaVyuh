"""Watchlist scanner engine."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from arthavyuh.core.config import (
    DEFAULT_DAILY_REPORTS_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_OHLCV_DIR,
    DEFAULT_WATCHLIST_PATH,
    load_strategy_settings,
    resolve_path,
)
from arthavyuh.core.models import Signal
from arthavyuh.data.loader import load_ohlcv, load_watchlist
from arthavyuh.database.repository import save_signals, save_symbols
from arthavyuh.reports.json_report import write_json_report
from arthavyuh.scanners.ranker import rank_signals
from arthavyuh.strategies.base import Strategy
from arthavyuh.strategies.registry import default_registry


def _select_strategies(strategy_name: str | None, run_all: bool) -> list[Strategy]:
    registry = default_registry()
    if run_all:
        return registry.list_strategies()
    if strategy_name:
        return [registry.get(strategy_name)]
    return registry.list_strategies()


def run_scan(
    strategy_name: str | None = None,
    run_all: bool = False,
    watchlist_path: str | Path = DEFAULT_WATCHLIST_PATH,
    ohlcv_dir: str | Path = DEFAULT_OHLCV_DIR,
    db_path: str | Path = DEFAULT_DB_PATH,
    reports_dir: str | Path = DEFAULT_DAILY_REPORTS_DIR,
    report_date: str | None = None,
) -> dict[str, Any]:
    """Run one or all strategies over a local watchlist."""

    selected_strategies = _select_strategies(strategy_name, run_all)
    selected_names = [strategy.name for strategy in selected_strategies]
    watchlist = load_watchlist(watchlist_path)
    save_symbols(watchlist, db_path)

    context = {
        "strategies": load_strategy_settings(),
    }

    signals: list[Signal] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    strategy_runs = 0

    for item in watchlist:
        symbol = item["symbol"]
        try:
            df = load_ohlcv(symbol, ohlcv_dir)
        except Exception as exc:
            skipped.append({"symbol": symbol, "reason": str(exc)})
            continue

        for strategy in selected_strategies:
            strategy_runs += 1
            try:
                signal = strategy.run(symbol, df, context)
                if signal is not None:
                    signals.append(signal)
            except Exception as exc:
                errors.append(
                    {
                        "symbol": symbol,
                        "strategy": strategy.name,
                        "reason": str(exc),
                    }
                )

    ranked = rank_signals(signals)
    save_signals(ranked, db_path)

    run_date = report_date or date.today().isoformat()
    reports_path = resolve_path(reports_dir)
    output_json_path = reports_path / f"signals_{run_date}.json"

    payload: dict[str, Any] = {
        "report_date": run_date,
        "summary": {
            "total_symbols_scanned": len(watchlist),
            "strategies_selected": selected_names,
            "total_strategies_run": strategy_runs,
            "signals_generated": len(ranked),
            "symbols_skipped_count": len(skipped),
            "symbols_skipped": skipped,
            "errors_count": len(errors),
            "errors": errors,
            "output_json_path": str(output_json_path),
        },
        "signals": [signal.model_dump(mode="json") for signal in ranked],
    }
    json_path = write_json_report(payload, reports_path, run_date)
    payload["summary"]["output_json_path"] = str(json_path)
    return payload
