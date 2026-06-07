"""Backtrader integration scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_backtest(data_path: str | Path, strategy_name: str) -> dict[str, Any]:
    """Return a placeholder result for future Backtrader implementations."""

    return {
        "status": "scaffold",
        "data_path": str(data_path),
        "strategy": strategy_name,
        "message": "Backtesting scaffold is present; strategy wiring is planned after scanner core stabilization.",
    }
