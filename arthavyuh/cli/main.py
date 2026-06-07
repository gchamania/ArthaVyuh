"""Typer CLI for ArthaVyuh."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from arthavyuh.brokers.dhan import (
    DEFAULT_DHAN_INSTRUMENTS_PATH,
    DhanReadOnlyClient,
    instruments_to_marketfeed_payload,
    load_dhan_instruments,
    write_historical_ohlcv_csv,
)
from arthavyuh.core.config import (
    DEFAULT_DAILY_REPORTS_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_OHLCV_DIR,
    DEFAULT_WATCHLIST_PATH,
)
from arthavyuh.core.exceptions import ConfigError
from arthavyuh.core.health import health_status_lines, run_health_check
from arthavyuh.database.db import initialize_database
from arthavyuh.database.repository import save_broker_snapshot
from arthavyuh.reports.evening_report import generate_evening_report
from arthavyuh.risk.position_sizing import calculate_position_size
from arthavyuh.scanners.scanner import run_scan
from arthavyuh.strategies.registry import default_registry

app = typer.Typer(help="ArthaVyuh deterministic trading core.")
strategies_app = typer.Typer(help="Strategy registry commands.")
report_app = typer.Typer(help="Report generation commands.")
risk_app = typer.Typer(help="Risk calculation commands.")
dhan_app = typer.Typer(help="Read-only DhanHQ data bridge.")
dhan_market_app = typer.Typer(help="Read-only DhanHQ market data commands.")
app.add_typer(strategies_app, name="strategies")
app.add_typer(report_app, name="report")
app.add_typer(risk_app, name="risk")
app.add_typer(dhan_app, name="dhan")
dhan_app.add_typer(dhan_market_app, name="market")

console = Console()


def _print_json(payload: dict) -> None:
    console.print(json.dumps(payload, indent=2))


def _fail(message: str, json_output: bool) -> None:
    if json_output:
        _print_json({"status": "FAIL", "error": message})
    else:
        console.print(f"FAIL {message}")
    raise typer.Exit(code=1)


def _dhan_client(json_output: bool) -> DhanReadOnlyClient:
    try:
        return DhanReadOnlyClient()
    except ConfigError as exc:
        _fail(str(exc), json_output)
        raise


def _dhan_api_call(json_output: bool, call):
    try:
        return call(_dhan_client(json_output))
    except typer.Exit:
        raise
    except RuntimeError as exc:
        _fail(str(exc), json_output)
        raise


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


@dhan_app.command("check")
def dhan_check(
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    """Check Dhan token/account visibility without placing orders."""

    profile = _dhan_api_call(json_output, lambda client: client.profile())
    payload = {"status": "PASS", "profile": profile}
    if json_output:
        _print_json(payload)
    else:
        console.print("PASS Dhan profile fetched")
        console.print(f"Client ID: {profile.get('dhanClientId', 'unknown')}")
        console.print(f"Token validity: {profile.get('tokenValidity', 'unknown')}")
        console.print(f"Data plan: {profile.get('dataPlan', 'unknown')}")


@dhan_app.command("holdings")
def dhan_holdings(
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    save: Annotated[bool, typer.Option("--save/--no-save", help="Save raw response snapshot.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    holdings = _dhan_api_call(json_output, lambda client: client.holdings())
    snapshot_id = save_broker_snapshot("dhan", "holdings", holdings, db_path=db_path) if save else None
    payload = {"status": "PASS", "count": len(holdings), "snapshot_id": snapshot_id, "holdings": holdings}
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS fetched {len(holdings)} holdings")
        if snapshot_id:
            console.print(f"Saved broker snapshot: {snapshot_id}")


@dhan_app.command("positions")
def dhan_positions(
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    save: Annotated[bool, typer.Option("--save/--no-save", help="Save raw response snapshot.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    positions = _dhan_api_call(json_output, lambda client: client.positions())
    snapshot_id = save_broker_snapshot("dhan", "positions", positions, db_path=db_path) if save else None
    payload = {"status": "PASS", "count": len(positions), "snapshot_id": snapshot_id, "positions": positions}
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS fetched {len(positions)} positions")
        if snapshot_id:
            console.print(f"Saved broker snapshot: {snapshot_id}")


@dhan_app.command("ledger")
def dhan_ledger(
    from_date: Annotated[str, typer.Option("--from-date", help="Start date, YYYY-MM-DD.")],
    to_date: Annotated[str, typer.Option("--to-date", help="End date, YYYY-MM-DD.")],
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    save: Annotated[bool, typer.Option("--save/--no-save", help="Save raw response snapshot.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    ledger = _dhan_api_call(json_output, lambda client: client.ledger(from_date, to_date))
    snapshot_id = (
        save_broker_snapshot("dhan", "ledger", ledger, from_date=from_date, to_date=to_date, db_path=db_path)
        if save
        else None
    )
    payload = {"status": "PASS", "count": len(ledger), "snapshot_id": snapshot_id, "ledger": ledger}
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS fetched {len(ledger)} ledger rows")
        if snapshot_id:
            console.print(f"Saved broker snapshot: {snapshot_id}")


@dhan_app.command("trades")
def dhan_trades(
    from_date: Annotated[str, typer.Option("--from-date", help="Start date, YYYY-MM-DD.")],
    to_date: Annotated[str, typer.Option("--to-date", help="End date, YYYY-MM-DD.")],
    page: Annotated[int, typer.Option("--page", help="Dhan trade history page number.")] = 0,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    save: Annotated[bool, typer.Option("--save/--no-save", help="Save raw response snapshot.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    trades = _dhan_api_call(json_output, lambda client: client.trades(from_date, to_date, page))
    snapshot_id = (
        save_broker_snapshot("dhan", "trades", trades, from_date=from_date, to_date=to_date, db_path=db_path)
        if save
        else None
    )
    payload = {"status": "PASS", "count": len(trades), "page": page, "snapshot_id": snapshot_id, "trades": trades}
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS fetched {len(trades)} trade rows on page {page}")
        if snapshot_id:
            console.print(f"Saved broker snapshot: {snapshot_id}")


@dhan_market_app.command("ltp")
def dhan_market_ltp(
    instruments: Annotated[Path, typer.Option("--instruments", help="Dhan instrument mapping CSV.")] = DEFAULT_DHAN_INSTRUMENTS_PATH,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    items = load_dhan_instruments(instruments)
    payload = _dhan_api_call(json_output, lambda client: client.market_ltp(instruments_to_marketfeed_payload(items)))
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS fetched LTP snapshot for {len(items)} instruments")


@dhan_market_app.command("ohlc")
def dhan_market_ohlc(
    instruments: Annotated[Path, typer.Option("--instruments", help="Dhan instrument mapping CSV.")] = DEFAULT_DHAN_INSTRUMENTS_PATH,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    items = load_dhan_instruments(instruments)
    payload = _dhan_api_call(json_output, lambda client: client.market_ohlc(instruments_to_marketfeed_payload(items)))
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS fetched OHLC snapshot for {len(items)} instruments")


@dhan_market_app.command("historical")
def dhan_market_historical(
    from_date: Annotated[str, typer.Option("--from-date", help="Start date, YYYY-MM-DD.")],
    to_date: Annotated[str, typer.Option("--to-date", help="End date, YYYY-MM-DD; Dhan treats it as non-inclusive.")],
    instruments: Annotated[Path, typer.Option("--instruments", help="Dhan instrument mapping CSV.")] = DEFAULT_DHAN_INSTRUMENTS_PATH,
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Where ArthaVyuh OHLCV CSVs are written.")] = DEFAULT_OHLCV_DIR,
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    client = _dhan_client(json_output)
    written: list[dict[str, str]] = []
    for item in load_dhan_instruments(instruments):
        try:
            response = client.historical_daily(
                security_id=item["security_id"],
                exchange_segment=item["exchange_segment"],
                instrument=item["instrument"],
                from_date=from_date,
                to_date=to_date,
            )
        except typer.Exit:
            raise
        except RuntimeError as exc:
            _fail(str(exc), json_output)
        path = write_historical_ohlcv_csv(item["symbol"], response, output_dir)
        written.append({"symbol": item["symbol"], "path": str(path)})

    payload = {"status": "PASS", "from_date": from_date, "to_date": to_date, "written": written}
    if json_output:
        _print_json(payload)
    else:
        console.print(f"PASS wrote {len(written)} OHLCV CSV files")
        for item in written:
            console.print(f"{item['symbol']}: {item['path']}")


if __name__ == "__main__":
    app()
