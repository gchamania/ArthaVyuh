"""Pydantic models used across the trading core."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arthavyuh.core.enums import SignalStatus

FORBIDDEN_LANGUAGE = (
    "buy now",
    "sell now",
    "strong buy",
    "guaranteed target",
    "sure shot",
    "high conviction call",
    "ai recommendation",
)


class Signal(BaseModel):
    """Standard scanner output.

    A signal is a structured setup record, not a trading recommendation.
    """

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    symbol: str
    strategy: str
    date: str
    status: SignalStatus
    score: int = Field(ge=0, le=100)

    close: float
    entry: float | None = None
    stop_loss: float | None = None
    target: float | None = None
    risk_reward: float | None = None

    reason: str
    invalidation: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("symbol", "strategy", "date", "reason")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be blank")
        return cleaned

    @field_validator("reason", "invalidation")
    @classmethod
    def reject_advisory_language(cls, value: str | None) -> str | None:
        if value is None:
            return value
        lowered = value.lower()
        for phrase in FORBIDDEN_LANGUAGE:
            if phrase in lowered:
                raise ValueError(f"non-advisory signal text cannot include '{phrase}'")
        return value.strip()
