"""Input data validation helpers."""

from __future__ import annotations

import pandas as pd

from arthavyuh.core.exceptions import DataValidationError

WATCHLIST_COLUMNS = {"symbol", "name"}
OHLCV_COLUMNS = {"date", "open", "high", "low", "close", "volume"}


def validate_watchlist(df: pd.DataFrame) -> None:
    missing = WATCHLIST_COLUMNS.difference(df.columns)
    if missing:
        raise DataValidationError(f"Watchlist missing columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise DataValidationError("Watchlist is empty")
    if df["symbol"].isna().any():
        raise DataValidationError("Watchlist contains blank symbols")


def validate_ohlcv(df: pd.DataFrame, symbol: str) -> None:
    missing = OHLCV_COLUMNS.difference(df.columns)
    if missing:
        raise DataValidationError(f"{symbol} OHLCV missing columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise DataValidationError(f"{symbol} OHLCV file is empty")

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        values = pd.to_numeric(df[column], errors="coerce")
        if values.isna().any():
            raise DataValidationError(f"{symbol} OHLCV column has non-numeric values: {column}")

    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.isna().any():
        raise DataValidationError(f"{symbol} OHLCV contains invalid dates")

    if (pd.to_numeric(df["high"], errors="coerce") < pd.to_numeric(df["low"], errors="coerce")).any():
        raise DataValidationError(f"{symbol} OHLCV has high below low")

    if (pd.to_numeric(df["close"], errors="coerce") <= 0).any():
        raise DataValidationError(f"{symbol} OHLCV has non-positive close values")
