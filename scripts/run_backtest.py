#!/usr/bin/env python
"""Run the backtesting scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arthavyuh.backtesting.backtrader_runner import run_backtest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--strategy", default="trend_pullback")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = run_backtest(args.data, args.strategy)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
