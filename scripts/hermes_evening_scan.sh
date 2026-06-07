#!/usr/bin/env bash
set -e

python scripts/health_check.py
python scripts/run_scanner.py --all --watchlist config/watchlists/sample_watchlist.csv
python scripts/generate_evening_report.py

echo "ArthaVyuh evening scan complete."
echo "Read reports/daily/latest.md and reports/daily/latest.json"
