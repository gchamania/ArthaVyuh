"""P/L helpers."""


def calculate_realized_pnl(entry_price: float, exit_price: float, quantity: int) -> float:
    return round((exit_price - entry_price) * quantity, 2)
