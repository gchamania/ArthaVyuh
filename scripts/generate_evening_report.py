#!/usr/bin/env python
"""Generate the ArthaVyuh evening report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arthavyuh.reports.evening_report import generate_evening_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = generate_evening_report()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PASS evening report generated")
        print(f"Markdown: {payload['markdown_path']}")
        print(f"Latest: {payload['latest_markdown_path']}")
        print(f"Latest JSON: {payload['latest_json_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
