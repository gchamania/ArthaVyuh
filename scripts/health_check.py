#!/usr/bin/env python
"""Run ArthaVyuh health checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arthavyuh.core.health import health_status_lines, run_health_check  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summary = run_health_check()
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for line in health_status_lines(summary):
            print(line)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
