"""Base strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from arthavyuh.core.models import Signal


class Strategy(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> Signal | None:
        """Run strategy logic and return a structured setup signal."""
