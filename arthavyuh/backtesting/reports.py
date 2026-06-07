"""Backtest report scaffold."""

from pathlib import Path


def backtest_report_path(run_id: str, reports_dir: str | Path = "reports/backtests") -> Path:
    return Path(reports_dir) / f"backtest_{run_id}.md"
