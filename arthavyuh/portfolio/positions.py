"""Position model scaffold."""

from pydantic import BaseModel


class Position(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    stop_loss: float | None = None
    target: float | None = None
