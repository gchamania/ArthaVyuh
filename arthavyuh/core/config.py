"""Configuration and path helpers."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from arthavyuh.core.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
DEFAULT_STRATEGIES_PATH = PROJECT_ROOT / "config" / "strategies.yaml"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "arthavyuh.db"
DEFAULT_WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlists" / "sample_watchlist.csv"
DEFAULT_OHLCV_DIR = PROJECT_ROOT / "data" / "ohlcv"
DEFAULT_DAILY_REPORTS_DIR = PROJECT_ROOT / "reports" / "daily"


def resolve_path(value: str | Path) -> Path:
    """Resolve a path relative to the project root when needed."""

    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise ConfigError(f"Config file not found: {resolved}")
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a mapping: {resolved}")
    return data


@lru_cache(maxsize=1)
def load_settings() -> dict[str, Any]:
    return load_yaml(DEFAULT_SETTINGS_PATH)


@lru_cache(maxsize=1)
def load_strategy_settings() -> dict[str, Any]:
    return load_yaml(DEFAULT_STRATEGIES_PATH).get("strategies", {})
