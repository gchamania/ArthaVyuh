"""Trend pullback strategy."""

from __future__ import annotations

from typing import Any

import pandas as pd

from arthavyuh.core.enums import SignalStatus
from arthavyuh.core.models import Signal
from arthavyuh.indicators import add_core_indicators
from arthavyuh.risk.position_sizing import calculate_reward_risk
from arthavyuh.strategies.base import Strategy


def _date_string(value: Any) -> str:
    if hasattr(value, "date"):
        return value.date().isoformat()
    return str(value)


class TrendPullbackStrategy(Strategy):
    name = "trend_pullback"
    description = "Find stocks in confirmed uptrend pulling back near moving average support."

    def run(self, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> Signal | None:
        if len(df) < 25:
            return None

        settings = context.get("strategies", {}).get(self.name, {})
        threshold = float(settings.get("pullback_threshold_percent", 3.0))
        min_rsi = float(settings.get("min_rsi", 40))
        max_rsi = float(settings.get("max_rsi", 65))

        enriched = add_core_indicators(df)
        last = enriched.iloc[-1]
        close = float(last["close"])
        ema20 = float(last["ema20"])
        ema50 = float(last["ema50"])
        ema200 = float(last["ema200"])
        rsi = float(last["rsi14"])
        relative_volume = float(last["relative_volume"])

        uptrend = close > ema50 > ema200
        near_ema20 = abs(close - ema20) / ema20 * 100 <= threshold
        near_ema50 = abs(close - ema50) / ema50 * 100 <= threshold
        pullback_quality = near_ema20 or near_ema50
        rsi_ok = min_rsi <= rsi <= max_rsi
        volume_ok = relative_volume >= 0.75

        entry = round(float(last["high"]) * 1.005, 2)
        stop_loss = round(min(float(last["low"]), ema50 * 0.98), 2)
        target = round(entry + (entry - stop_loss) * 2, 2)
        risk_reward = calculate_reward_risk(entry, stop_loss, target)
        risk_ok = risk_reward is not None and risk_reward >= 1.5 and stop_loss < entry

        score = 0
        score += 25 if uptrend else 0
        score += 25 if pullback_quality else 0
        score += 20 if rsi_ok else 0
        score += 15 if volume_ok else 0
        score += 15 if risk_ok else 0

        if uptrend and pullback_quality and rsi_ok and volume_ok and risk_ok:
            status = SignalStatus.ACTIONABLE
            reason = "setup detected: uptrend pullback near moving average support with risk check passed"
            invalidation = "risk check failed if price closes below the planned stop-loss zone"
            tags = ["trend", "pullback", "risk_check_passed"]
        elif uptrend and pullback_quality:
            status = SignalStatus.WATCHLIST
            reason = "watchlist candidate: trend structure present, entry trigger pending"
            invalidation = "setup weakens if trend structure or pullback support fails"
            tags = ["trend", "pullback", "entry_trigger_pending"]
        else:
            status = SignalStatus.AVOID
            reason = "risk check failed or setup conditions are weak for self-directed analysis"
            invalidation = "reassess only after trend and pullback conditions improve"
            tags = ["avoid", "structure_weak"]

        return Signal(
            symbol=symbol,
            strategy=self.name,
            date=_date_string(last["date"]),
            status=status,
            score=min(score, 100),
            close=round(close, 2),
            entry=entry if status != SignalStatus.AVOID else None,
            stop_loss=stop_loss if status != SignalStatus.AVOID else None,
            target=target if status != SignalStatus.AVOID else None,
            risk_reward=risk_reward if status != SignalStatus.AVOID else None,
            reason=reason,
            invalidation=invalidation,
            tags=tags,
        )
