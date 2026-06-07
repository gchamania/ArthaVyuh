"""Evening report generation."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from arthavyuh.core.config import DEFAULT_DAILY_REPORTS_DIR, DEFAULT_DB_PATH, resolve_path
from arthavyuh.database.repository import save_daily_report_metadata
from arthavyuh.reports.markdown import render_evening_report


def _empty_payload(report_date: str) -> dict[str, Any]:
    return {
        "report_date": report_date,
        "summary": {
            "total_symbols_scanned": 0,
            "strategies_selected": [],
            "total_strategies_run": 0,
            "signals_generated": 0,
            "symbols_skipped_count": 0,
            "symbols_skipped": [],
            "errors_count": 0,
            "errors": [],
            "output_json_path": "",
        },
        "signals": [],
    }


def load_latest_scan_payload(reports_dir: str | Path = DEFAULT_DAILY_REPORTS_DIR) -> dict[str, Any] | None:
    latest_path = resolve_path(reports_dir) / "latest.json"
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text(encoding="utf-8"))


def generate_evening_report(
    payload: dict[str, Any] | None = None,
    reports_dir: str | Path = DEFAULT_DAILY_REPORTS_DIR,
    db_path: str | Path = DEFAULT_DB_PATH,
    report_date: str | None = None,
) -> dict[str, Any]:
    resolved_dir = resolve_path(reports_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)

    run_date = report_date or date.today().isoformat()
    scan_payload = payload or load_latest_scan_payload(resolved_dir) or _empty_payload(run_date)
    scan_payload["report_date"] = scan_payload.get("report_date") or run_date
    run_date = scan_payload["report_date"]

    markdown = render_evening_report(scan_payload)
    markdown_path = resolved_dir / f"evening_report_{run_date}.md"
    markdown_path.write_text(markdown, encoding="utf-8")
    latest_markdown_path = resolved_dir / "latest.md"
    shutil.copyfile(markdown_path, latest_markdown_path)

    latest_json_path = resolved_dir / "latest.json"
    total_symbols = int(scan_payload.get("summary", {}).get("total_symbols_scanned", 0))
    total_signals = int(scan_payload.get("summary", {}).get("signals_generated", 0))
    save_daily_report_metadata(
        run_date,
        markdown_path,
        latest_json_path,
        total_symbols,
        total_signals,
        db_path,
    )

    return {
        "status": "PASS",
        "report_date": run_date,
        "markdown_path": str(markdown_path),
        "latest_markdown_path": str(latest_markdown_path),
        "latest_json_path": str(latest_json_path),
        "total_symbols_scanned": total_symbols,
        "total_signals": total_signals,
    }
