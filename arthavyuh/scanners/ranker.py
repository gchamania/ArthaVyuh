"""Signal ranking helpers."""

from arthavyuh.core.models import Signal

STATUS_PRIORITY = {"actionable": 0, "watchlist": 1, "avoid": 2}


def rank_signals(signals: list[Signal]) -> list[Signal]:
    return sorted(
        signals,
        key=lambda signal: (
            STATUS_PRIORITY.get(str(signal.status), 3),
            -signal.score,
            signal.symbol,
            signal.strategy,
        ),
    )
