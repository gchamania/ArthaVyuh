"""Momentum indicators."""

from __future__ import annotations

import pandas as pd
import numpy as np


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    values = 100 - (100 / (1 + rs))
    return values.fillna(50)


def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = pd.to_numeric(enriched["close"], errors="raise")
    enriched["rsi14"] = rsi(close, 14)
    enriched["return_20d"] = close.pct_change(20).fillna(0)
    return enriched
