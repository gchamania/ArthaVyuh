"""Indicator helpers."""

from __future__ import annotations

import pandas as pd

from arthavyuh.indicators.momentum import add_momentum_indicators
from arthavyuh.indicators.moving_averages import add_moving_averages
from arthavyuh.indicators.volatility import add_volatility_indicators
from arthavyuh.indicators.volume import add_volume_indicators


def add_core_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add indicators needed by v0.1 strategies."""

    enriched = add_moving_averages(df)
    enriched = add_momentum_indicators(enriched)
    enriched = add_volatility_indicators(enriched)
    enriched = add_volume_indicators(enriched)
    return enriched


__all__ = ["add_core_indicators"]
