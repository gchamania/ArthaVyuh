#!/usr/bin/env python
"""Initialize the ArthaVyuh SQLite database."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arthavyuh.core.config import DEFAULT_DB_PATH  # noqa: E402
from arthavyuh.database.db import initialize_database  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = initialize_database(args.db_path)
    payload = {"status": "PASS", "db_path": str(path)}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"PASS database initialized: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
