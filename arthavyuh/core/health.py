"""Health checks for local and Hermes-driven workflows."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from arthavyuh.core.config import (
    DEFAULT_DAILY_REPORTS_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_OHLCV_DIR,
    DEFAULT_SETTINGS_PATH,
    DEFAULT_STRATEGIES_PATH,
    DEFAULT_WATCHLIST_PATH,
)
from arthavyuh.database.db import initialize_database
from arthavyuh.strategies.registry import default_registry

REQUIRED_IMPORTS = ("pandas", "numpy", "pydantic", "typer", "rich", "yaml", "backtrader")
SAMPLE_OHLCV_FILES = (
    "DEMO_RELIANCE.csv",
    "DEMO_TCS.csv",
    "DEMO_HDFCBANK.csv",
)


def _check(name: str, passed: bool, message: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "message": message}


def run_health_check() -> dict[str, Any]:
    """Return a machine-readable PASS/FAIL health summary."""

    checks: list[dict[str, Any]] = []

    version_ok = sys.version_info >= (3, 11)
    checks.append(
        _check(
            "python_version",
            version_ok,
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
            checks.append(_check(f"import_{module_name}", True, f"{module_name} import ok"))
        except Exception as exc:  # pragma: no cover - exercised when deps are missing
            checks.append(_check(f"import_{module_name}", False, str(exc)))

    required_files = (
        DEFAULT_SETTINGS_PATH,
        DEFAULT_STRATEGIES_PATH,
        DEFAULT_WATCHLIST_PATH,
    )
    for path in required_files:
        checks.append(_check(f"file_{path.name}", path.exists(), str(path)))

    for filename in SAMPLE_OHLCV_FILES:
        path = DEFAULT_OHLCV_DIR / filename
        checks.append(_check(f"ohlcv_{filename}", path.exists(), str(path)))

    DEFAULT_DAILY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    checks.append(
        _check(
            "reports_directory",
            DEFAULT_DAILY_REPORTS_DIR.exists(),
            str(DEFAULT_DAILY_REPORTS_DIR),
        )
    )

    try:
        initialize_database(DEFAULT_DB_PATH)
        db_ok = DEFAULT_DB_PATH.exists()
        checks.append(_check("database", db_ok, str(DEFAULT_DB_PATH)))
    except Exception as exc:
        checks.append(_check("database", False, str(exc)))

    try:
        registry = default_registry()
        strategy_names = registry.list_names()
        checks.append(
            _check(
                "strategies_registered",
                len(strategy_names) >= 3,
                ", ".join(strategy_names),
            )
        )
    except Exception as exc:
        checks.append(_check("strategies_registered", False, str(exc)))

    passed = all(item["passed"] for item in checks)
    return {
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
    }


def health_status_lines(summary: dict[str, Any]) -> list[str]:
    lines = [f"ArthaVyuh health: {summary['status']}"]
    for check in summary["checks"]:
        marker = "PASS" if check["passed"] else "FAIL"
        lines.append(f"{marker} {check['name']}: {check['message']}")
    return lines
