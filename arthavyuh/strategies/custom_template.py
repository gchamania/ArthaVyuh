"""Template for future deterministic strategies."""

from __future__ import annotations

from typing import Any

import pandas as pd

from arthavyuh.core.models import Signal
from arthavyuh.strategies.base import Strategy


class CustomTemplateStrategy(Strategy):
    name = "custom_template"
    description = "Template only; not registered by default."

    def run(self, symbol: str, df: pd.DataFrame, context: dict[str, Any]) -> Signal | None:
        return None
