"""Volume indicators."""

from __future__ import annotations

import pandas as pd


def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    volume = pd.to_numeric(enriched["volume"], errors="raise")
    enriched["avg_volume20"] = volume.rolling(window=20, min_periods=1).mean()
    enriched["relative_volume"] = (volume / enriched["avg_volume20"].replace(0, pd.NA)).fillna(0)
    return enriched
