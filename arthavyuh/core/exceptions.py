"""Project-specific exceptions."""


class ArthaVyuhError(Exception):
    """Base exception for ArthaVyuh errors."""


class ConfigError(ArthaVyuhError):
    """Raised when configuration cannot be loaded or validated."""


class DataValidationError(ArthaVyuhError):
    """Raised when input data does not match expected schema."""


class StrategyError(ArthaVyuhError):
    """Raised when a strategy cannot complete."""


class DatabaseError(ArthaVyuhError):
    """Raised when SQLite operations fail."""
