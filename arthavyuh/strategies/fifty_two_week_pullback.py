"""52-week high pullback strategy."""

from __future__ import annotations

from typing import Any

import pandas as pd

from arthavyuh.core.enums import SignalStatus
from arthavyuh.core.models import Signal
from arthavyuh.indicators import add_core_indicators
from arthavyuh.strategies.base import Strategy
from arthavyuh.strategies.trend_pullback import _date_string


class FiftyTwoWeekPullbackStrategy(Strategy):
    name = "fifty_two_week_pullback"
    description = "Find strong stocks near 52-week highs after a controlled pullback."

    def run(self, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> Signal | None:
        if len(df) < 30:
            return None

        settings = context.get("strategies", {}).get(self.name, {})
        near_high_threshold = float(settings.get("near_high_threshold_percent", 15.0))
        max_rsi = float(settings.get("max_rsi", 72))

        enriched = add_core_indicators(df)
        last = enriched.iloc[-1]
        lookback = min(252, len(enriched))
        lookback_slice = enriched.tail(lookback)

        high_52 = float(lookback_slice["high"].max())
        close = float(last["close"])
        ema50 = float(last["ema50"])
        ema200 = float(last["ema200"])
        rsi = float(last["rsi14"])

        distance_from_high = (high_52 - close) / high_52 * 100
        near_high = distance_from_high <= near_high_threshold
        controlled_pullback = 1.0 <= distance_from_high <= near_high_threshold
        uptrend = close > ema50 > ema200
        rsi_ok = rsi <= max_rsi

        score = 0
        score += 30 if near_high else 0
        score += 25 if uptrend else 0
        score += 25 if controlled_pullback else 0
        score += 20 if rsi_ok else 0

        if near_high and uptrend and controlled_pullback and rsi_ok:
            status = SignalStatus.WATCHLIST
            reason = "watchlist candidate: near high structure with controlled pullback; entry trigger pending"
            invalidation = "setup weakens if price loses the moving average trend structure"
            tags = ["near_high", "pullback", "entry_trigger_pending"]
        else:
            status = SignalStatus.AVOID
            reason = "setup conditions are weak for the near high pullback scan"
            invalidation = "reassess after trend structure and controlled pullback conditions improve"
            tags = ["avoid", "near_high_structure_weak"]

        return Signal(
            symbol=symbol,
            strategy=self.name,
            date=_date_string(last["date"]),
            status=status,
            score=min(score, 100),
            close=round(close, 2),
            reason=reason,
            invalidation=invalidation,
            tags=tags,
        )
