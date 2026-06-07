# ArthaVyuh

ArthaVyuh is an experimental, local-first swing trading cockpit for self-directed retail traders.

Structure before signal.

ArthaVyuh v0.1 is a deterministic Python trading core. It scans local watchlists, reads local OHLCV CSVs, calculates rule-based setup candidates, validates basic risk, stores signals in SQLite, and generates JSON/Markdown reports.

It is not investment advice. It does not provide buy/sell calls. It does not guarantee returns. Use at your own risk.

## Quickstart

```bash
git clone https://github.com/<username>/arthavyuh.git
cd arthavyuh

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .

arthavyuh init-db
arthavyuh health
arthavyuh scan --all --watchlist config/watchlists/sample_watchlist.csv
arthavyuh report evening
pytest
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pip install -e .
```

## CLI

```bash
arthavyuh init-db
arthavyuh health
arthavyuh strategies list
arthavyuh scan --strategy trend_pullback --watchlist config/watchlists/sample_watchlist.csv
arthavyuh scan --all --watchlist config/watchlists/sample_watchlist.csv
arthavyuh report evening
arthavyuh risk size --capital 100000 --risk-percent 1 --entry 500 --stop 475
```

Use `--json` on machine-facing commands where available.

## DhanHQ Read-Only Bridge

ArthaVyuh can optionally ingest read-only Dhan account and market data. It does not place, modify, cancel, or execute broker orders.

Set credentials in your shell or a local `.env` loader:

```bash
export DHAN_CLIENT_ID="your-client-id"
export DHAN_ACCESS_TOKEN="your-access-token"
```

Read-only commands:

```bash
arthavyuh dhan check
arthavyuh dhan holdings --json
arthavyuh dhan positions --json
arthavyuh dhan ledger --from-date 2026-06-01 --to-date 2026-06-07 --json
arthavyuh dhan trades --from-date 2026-06-01 --to-date 2026-06-07 --json
arthavyuh dhan market historical --from-date 2025-01-01 --to-date 2025-12-31 --instruments config/dhan_instruments_sample.csv
```

Historical market data writes ArthaVyuh-compatible OHLCV CSV files into `data/ohlcv/` by default.

Configure instrument mappings in:

```text
config/dhan_instruments_sample.csv
```

## Data

Watchlists live in `config/watchlists/` and use:

```csv
symbol,name
DEMO_RELIANCE,Reliance Demo
```

OHLCV files live in `data/ohlcv/` and use:

```csv
date,open,high,low,close,volume
2025-01-01,100,105,99,104,1000000
```

## Safety Boundary

ArthaVyuh is for self-directed analysis only. Reports and signals use non-advisory language such as "setup detected", "watchlist candidate", "risk check passed", and "entry trigger pending".

ArthaVyuh must not:

- place broker orders
- invent prices
- call anything a guaranteed trade
- provide buy/sell recommendations
- depend on Hermes, OpenAlgo, or broker APIs
