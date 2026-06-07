"""Journal review helpers."""

from arthavyuh.journal.trade_journal import JournalEntry


def collect_lessons(entries: list[JournalEntry]) -> list[str]:
    return [entry.lesson for entry in entries if entry.lesson]
