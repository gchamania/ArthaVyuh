"""Typer CLI for ArthaVyuh."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from arthavyuh.core.config import (
    DEFAULT_DAILY_REPORTS_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_OHLCV_DIR,
    DEFAULT_WATCHLIST_PATH,
)
from arthavyuh.core.health import health_status_lines, run_health_check
from arthavyuh.database.db import initialize_database
from arthavyuh.reports.evening_report import generate_evening_report
from arthavyuh.risk.position_sizing import calculate_position_size
from arthavyuh.scanners.scanner import run_scan
from arthavyuh.strategies.registry import default_registry

app = typer.Typer(help="ArthaVyuh deterministic trading core.")
strategies_app = typer.Typer(help="Strategy registry commands.")
report_app = typer.Typer(help="Report generation commands.")
risk_app = typer.Typer(help="Risk calculation commands.")
app.add_typer(strategies_app, name="strategies")
app.add_typer(report_app, name="report")
app.add_typer(risk_app, name="risk")

console = Console()


def _print_json(payload: dict) -> None:
    console.print(json.dumps(payload, indent=2))


@app.command("init-db")
def init_db(
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    path = initialize_database(db_path)
    payload = {"status": "PASS", "db_path": str(path)}
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS database initialized: {path}")


@app.command("health")
def health(
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    summary = run_health_check()
    if json_output:
        _print_json(summary)
    else:
        for line in health_status_lines(summary):
            console.print(line)
    if summary["status"] != "PASS":
        raise typer.Exit(code=1)


@strategies_app.command("list")
def list_strategies(
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    registry = default_registry()
    strategies = [
        {"name": strategy.name, "description": strategy.description}
        for strategy in registry.list_strategies()
    ]
    if json_output:
        _print_json({"strategies": strategies})
        return

    table = Table(title="Registered Strategies")
    table.add_column("Name")
    table.add_column("Description")
    for strategy in strategies:
        table.add_row(strategy["name"], strategy["description"])
    console.print(table)


@app.command("scan")
def scan(
    strategy: Annotated[str | None, typer.Option("--strategy", help="Strategy name to run.")] = None,
    all_strategies: Annotated[bool, typer.Option("--all", help="Run all registered strategies.")] = False,
    watchlist: Annotated[Path, typer.Option("--watchlist", help="Watchlist CSV path.")] = DEFAULT_WATCHLIST_PATH,
    ohlcv_dir: Annotated[Path, typer.Option("--ohlcv-dir", help="OHLCV CSV directory.")] = DEFAULT_OHLCV_DIR,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    reports_dir: Annotated[Path, typer.Option("--reports-dir", help="Daily reports directory.")] = DEFAULT_DAILY_REPORTS_DIR,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    if strategy and all_strategies:
        raise typer.BadParameter("Use either --strategy or --all, not both.")

    payload = run_scan(
        strategy_name=strategy,
        run_all=all_strategies or strategy is None,
        watchlist_path=watchlist,
        ohlcv_dir=ohlcv_dir,
        db_path=db_path,
        reports_dir=reports_dir,
    )

    if json_output:
        _print_json(payload)
        return

    summary = payload["summary"]
    console.print("ArthaVyuh scan complete")
    console.print(f"Total symbols scanned: {summary['total_symbols_scanned']}")
    console.print(f"Total strategy runs: {summary['total_strategies_run']}")
    console.print(f"Signals generated: {summary['signals_generated']}")
    console.print(f"Symbols skipped: {summary['symbols_skipped_count']}")
    console.print(f"Errors: {summary['errors_count']}")
    console.print(f"Output JSON: {summary['output_json_path']}")


@report_app.command("evening")
def evening_report(
    reports_dir: Annotated[Path, typer.Option("--reports-dir", help="Daily reports directory.")] = DEFAULT_DAILY_REPORTS_DIR,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    payload = generate_evening_report(reports_dir=reports_dir, db_path=db_path)
    if json_output:
        _print_json(payload)
    else:
        console.print("PASS evening report generated")
        console.print(f"Markdown: {payload['markdown_path']}")
        console.print(f"Latest: {payload['latest_markdown_path']}")
        console.print(f"Latest JSON: {payload['latest_json_path']}")


@risk_app.command("size")
def risk_size(
    capital: Annotated[float, typer.Option("--capital", help="Trading capital.")],
    risk_percent: Annotated[float, typer.Option("--risk-percent", help="Risk percent per trade plan.")],
    entry: Annotated[float, typer.Option("--entry", help="Entry trigger price.")],
    stop: Annotated[float, typer.Option("--stop", help="Stop-loss price.")],
    target: Annotated[float | None, typer.Option("--target", help="Optional target price.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    result = calculate_position_size(capital, risk_percent, entry, stop, target)
    payload = result.model_dump(mode="json")
    if json_output:
        _print_json(payload)
        return

    marker = "PASS" if result.valid else "FAIL"
    console.print(f"{marker} {result.reason}")
    console.print(f"Quantity: {result.quantity}")
    console.print(f"Capital required: {result.capital_required}")
    console.print(f"Risk amount: {result.risk_amount}")
    if result.risk_reward is not None:
        console.print(f"Risk:reward: {result.risk_reward}")


if __name__ == "__main__":
    app()
