"""Shared enumerations."""

from enum import StrEnum


class SignalStatus(StrEnum):
    """Allowed scanner signal states."""

    ACTIONABLE = "actionable"
    WATCHLIST = "watchlist"
    AVOID = "avoid"
