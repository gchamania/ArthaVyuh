"""Portfolio exposure helpers."""


def exposure_percent(capital: float, capital_required: float) -> float:
    if capital <= 0:
        return 0.0
    return round(capital_required / capital * 100, 2)
