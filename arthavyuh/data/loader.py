"""Load local watchlist and OHLCV CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from arthavyuh.core.config import DEFAULT_OHLCV_DIR, DEFAULT_WATCHLIST_PATH, resolve_path
from arthavyuh.core.exceptions import DataValidationError
from arthavyuh.data.validators import validate_ohlcv, validate_watchlist


def load_watchlist(path: str | Path = DEFAULT_WATCHLIST_PATH) -> list[dict[str, str]]:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise DataValidationError(f"Watchlist not found: {resolved}")

    df = pd.read_csv(resolved)
    validate_watchlist(df)
    df = df.copy()
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    return df[["symbol", "name"]].to_dict(orient="records")


def load_ohlcv(symbol: str, ohlcv_dir: str | Path = DEFAULT_OHLCV_DIR) -> pd.DataFrame:
    directory = resolve_path(ohlcv_dir)
    path = directory / f"{symbol}.csv"
    if not path.exists():
        raise DataValidationError(f"OHLCV file not found for {symbol}: {path}")

    df = pd.read_csv(path)
    validate_ohlcv(df, symbol)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="raise")
    return df.sort_values("date").reset_index(drop=True)
