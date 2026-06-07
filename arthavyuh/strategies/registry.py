"""Strategy registration and execution."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from arthavyuh.core.models import Signal
from arthavyuh.strategies.base import Strategy
from arthavyuh.strategies.breakout_retest import BreakoutRetestStrategy
from arthavyuh.strategies.fifty_two_week_pullback import FiftyTwoWeekPullbackStrategy
from arthavyuh.strategies.trend_pullback import TrendPullbackStrategy


class StrategyRegistry:
    """In-memory strategy registry for deterministic scanner runs."""

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        if strategy.name in self._strategies:
            raise ValueError(f"Strategy already registered: {strategy.name}")
        self._strategies[strategy.name] = strategy

    def list_names(self) -> list[str]:
        return sorted(self._strategies)

    def list_strategies(self) -> list[Strategy]:
        return [self._strategies[name] for name in self.list_names()]

    def get(self, name: str) -> Strategy:
        try:
            return self._strategies[name]
        except KeyError as exc:
            available = ", ".join(self.list_names())
            raise KeyError(f"Unknown strategy '{name}'. Available: {available}") from exc

    def run(self, name: str, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> Signal | None:
        return self.get(name).run(symbol, df, context)

    def run_all(self, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> list[Signal]:
        signals: list[Signal] = []
        for strategy in self.list_strategies():
            signal = strategy.run(symbol, df, context)
            if signal is not None:
                signals.append(signal)
        return signals


@lru_cache(maxsize=1)
def default_registry() -> StrategyRegistry:
    registry = StrategyRegistry()
    registry.register(TrendPullbackStrategy())
    registry.register(BreakoutRetestStrategy())
    registry.register(FiftyTwoWeekPullbackStrategy())
    return registry
