"""Moving average indicators."""

from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=1).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = pd.to_numeric(enriched["close"], errors="raise")
    enriched["ema20"] = ema(close, 20)
    enriched["ema50"] = ema(close, 50)
    enriched["ema200"] = ema(close, 200)
    enriched["sma20"] = sma(close, 20)
    return enriched
