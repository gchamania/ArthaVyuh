"""Volatility indicators."""

from __future__ import annotations

import pandas as pd


def average_true_range(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = pd.to_numeric(df["high"], errors="raise")
    low = pd.to_numeric(df["low"], errors="raise")
    close = pd.to_numeric(df["close"], errors="raise")
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=period, min_periods=1).mean()


def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["atr14"] = average_true_range(enriched, 14)
    return enriched
