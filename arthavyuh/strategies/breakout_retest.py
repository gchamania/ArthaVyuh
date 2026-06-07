"""Breakout retest strategy."""

from __future__ import annotations

from typing import Any

import pandas as pd

from arthavyuh.core.enums import SignalStatus
from arthavyuh.core.models import Signal
from arthavyuh.indicators import add_core_indicators
from arthavyuh.risk.position_sizing import calculate_reward_risk
from arthavyuh.strategies.base import Strategy
from arthavyuh.strategies.trend_pullback import _date_string


class BreakoutRetestStrategy(Strategy):
    name = "breakout_retest"
    description = "Find recent breakouts retesting the previous resistance zone."

    def run(self, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> Signal | None:
        settings = context.get("strategies", {}).get(self.name, {})
        lookback = int(settings.get("lookback", 20))
        recent_days = int(settings.get("breakout_recent_days", 8))
        threshold = float(settings.get("retest_threshold_percent", 3.0))

        if len(df) < lookback + recent_days + 2:
            return None

        enriched = add_core_indicators(df)
        last = enriched.iloc[-1]
        resistance_window = enriched.iloc[-(lookback + recent_days) : -recent_days]
        recent_window = enriched.iloc[-recent_days:]

        resistance = float(resistance_window["high"].max())
        breakout_rows = recent_window[
            (recent_window["close"] > resistance * 1.01)
            & (recent_window["volume"] > recent_window["avg_volume20"] * 1.15)
        ]
        breakout_happened = not breakout_rows.empty

        close = float(last["close"])
        retest_distance = abs(close - resistance) / resistance * 100
        near_breakout_zone = retest_distance <= threshold
        holding_zone = close >= resistance * 0.98
        volume_ok = float(last["relative_volume"]) >= 0.75

        entry = round(float(last["high"]) * 1.003, 2)
        stop_loss = round(min(float(last["low"]), resistance * 0.97), 2)
        target = round(entry + (entry - stop_loss) * 2, 2)
        risk_reward = calculate_reward_risk(entry, stop_loss, target)
        risk_ok = risk_reward is not None and risk_reward >= 1.5 and stop_loss < entry

        score = 0
        score += 30 if breakout_happened else 0
        score += 25 if near_breakout_zone else 0
        score += 15 if holding_zone else 0
        score += 15 if volume_ok else 0
        score += 15 if risk_ok else 0

        if breakout_happened and near_breakout_zone and holding_zone and volume_ok and risk_ok:
            status = SignalStatus.ACTIONABLE
            reason = "setup detected: breakout retest holding above prior resistance with risk check passed"
            invalidation = "risk check failed if price loses the retest low or prior resistance zone"
            tags = ["breakout", "retest", "risk_check_passed"]
        elif breakout_happened and holding_zone:
            status = SignalStatus.WATCHLIST
            reason = "watchlist candidate: breakout structure found, entry trigger pending"
            invalidation = "setup weakens if price fails to hold the prior resistance zone"
            tags = ["breakout", "entry_trigger_pending"]
        else:
            status = SignalStatus.AVOID
            reason = "setup conditions are weak; breakout retest structure not confirmed"
            invalidation = "reassess after a clean breakout and retest structure forms"
            tags = ["avoid", "breakout_structure_weak"]

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
