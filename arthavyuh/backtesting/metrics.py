"""Backtest metric helpers."""


def win_rate(wins: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(wins / total * 100, 2)
