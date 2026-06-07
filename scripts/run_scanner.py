#!/usr/bin/env python
"""Run the ArthaVyuh scanner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arthavyuh.core.config import DEFAULT_WATCHLIST_PATH  # noqa: E402
from arthavyuh.scanners.scanner import run_scan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy")
    parser.add_argument("--all", action="store_true", dest="all_strategies")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = run_scan(
        strategy_name=args.strategy,
        run_all=args.all_strategies or args.strategy is None,
        watchlist_path=args.watchlist,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        summary = payload["summary"]
        print("ArthaVyuh scan complete")
        print(f"Total symbols scanned: {summary['total_symbols_scanned']}")
        print(f"Total strategy runs: {summary['total_strategies_run']}")
        print(f"Signals generated: {summary['signals_generated']}")
        print(f"Symbols skipped: {summary['symbols_skipped_count']}")
        print(f"Errors: {summary['errors_count']}")
        print(f"Output JSON: {summary['output_json_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
