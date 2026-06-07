"""Reusable risk validation rules."""

from arthavyuh.risk.position_sizing import PositionSizeResult, calculate_position_size


def validate_long_trade_plan(
    capital: float,
    risk_percent: float,
    entry: float,
    stop_loss: float,
    target: float | None = None,
) -> PositionSizeResult:
    return calculate_position_size(capital, risk_percent, entry, stop_loss, target)
