import pytest
from pydantic import ValidationError

from arthavyuh.core.models import Signal


def test_signal_model_accepts_valid_signal() -> None:
    signal = Signal(
        symbol="DEMO_RELIANCE",
        strategy="trend_pullback",
        date="2025-02-14",
        status="watchlist",
        score=72,
        close=128.0,
        reason="watchlist candidate: entry trigger pending",
        tags=["watchlist"],
    )

    assert signal.status == "watchlist"
    assert signal.score == 72


def test_signal_model_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        Signal(
            symbol="DEMO_RELIANCE",
            strategy="trend_pullback",
            date="2025-02-14",
            status="strong_buy",
            score=72,
            close=128.0,
            reason="watchlist candidate",
        )


def test_signal_model_rejects_advisory_language() -> None:
    with pytest.raises(ValidationError):
        Signal(
            symbol="DEMO_RELIANCE",
            strategy="trend_pullback",
            date="2025-02-14",
            status="watchlist",
            score=72,
            close=128.0,
            reason="buy now",
        )
