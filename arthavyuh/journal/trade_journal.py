"""Manual trade journal scaffold."""

from pydantic import BaseModel, Field


class JournalEntry(BaseModel):
    trade_id: int | None = None
    emotion: str | None = None
    reason_for_trade: str
    mistake_tags: list[str] = Field(default_factory=list)
    lesson: str | None = None
