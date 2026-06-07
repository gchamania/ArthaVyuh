"""Position sizing calculations."""

from __future__ import annotations

from math import floor

from pydantic import BaseModel


class PositionSizeResult(BaseModel):
    valid: bool
    reason: str
    capital: float
    risk_percent: float
    risk_amount: float
    entry: float
    stop_loss: float
    risk_per_share: float
    quantity: int
    capital_required: float
    target: float | None = None
    risk_reward: float | None = None


def calculate_reward_risk(entry: float, stop_loss: float, target: float | None) -> float | None:
    if target is None:
        return None
    risk_per_share = entry - stop_loss
    if entry <= 0 or stop_loss <= 0 or target <= entry or risk_per_share <= 0:
        return None
    return round((target - entry) / risk_per_share, 2)


def _invalid(
    reason: str,
    capital: float,
    risk_percent: float,
    entry: float,
    stop_loss: float,
    target: float | None = None,
) -> PositionSizeResult:
    risk_amount = capital * risk_percent / 100 if capital > 0 and risk_percent > 0 else 0
    risk_per_share = entry - stop_loss
    return PositionSizeResult(
        valid=False,
        reason=reason,
        capital=capital,
        risk_percent=risk_percent,
        risk_amount=round(risk_amount, 2),
        entry=entry,
        stop_loss=stop_loss,
        risk_per_share=round(risk_per_share, 2),
        quantity=0,
        capital_required=0,
        target=target,
        risk_reward=calculate_reward_risk(entry, stop_loss, target),
    )


def calculate_position_size(
    capital: float,
    risk_percent: float,
    entry: float,
    stop_loss: float,
    target: float | None = None,
) -> PositionSizeResult:
    """Calculate long-only position size without recommending a trade."""

    if capital <= 0:
        return _invalid("capital must be positive", capital, risk_percent, entry, stop_loss, target)
    if risk_percent <= 0:
        return _invalid("risk percent must be positive", capital, risk_percent, entry, stop_loss, target)
    if entry <= 0:
        return _invalid("entry must be positive", capital, risk_percent, entry, stop_loss, target)
    if stop_loss <= 0:
        return _invalid("stop-loss must be positive", capital, risk_percent, entry, stop_loss, target)
    if stop_loss >= entry:
        return _invalid("stop-loss must be below entry for a long trade plan", capital, risk_percent, entry, stop_loss, target)

    risk_amount = capital * risk_percent / 100
    risk_per_share = entry - stop_loss
    if risk_per_share <= 0:
        return _invalid("risk per share must be positive", capital, risk_percent, entry, stop_loss, target)

    quantity = floor(risk_amount / risk_per_share)
    if quantity <= 0:
        return _invalid("quantity is zero because risk amount is too small", capital, risk_percent, entry, stop_loss, target)

    capital_required = quantity * entry
    return PositionSizeResult(
        valid=True,
        reason="risk check passed",
        capital=round(capital, 2),
        risk_percent=round(risk_percent, 4),
        risk_amount=round(risk_amount, 2),
        entry=round(entry, 2),
        stop_loss=round(stop_loss, 2),
        risk_per_share=round(risk_per_share, 2),
        quantity=quantity,
        capital_required=round(capital_required, 2),
        target=round(target, 2) if target is not None else None,
        risk_reward=calculate_reward_risk(entry, stop_loss, target),
    )
