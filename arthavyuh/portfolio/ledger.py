"""Trade ledger scaffold."""

from pydantic import BaseModel


class LedgerEntry(BaseModel):
    symbol: str
    quantity: int
    entry_price: float
    exit_price: float | None = None
    notes: str | None = None
