# ArthaVyuh Agent Instructions

ArthaVyuh is an open-source, local-first swing trading cockpit for self-directed retail traders.

## Core Principle

Structure before signal.

This project is not a stock-tip service, not an investment adviser, not an auto-trading bot, and not a broker execution engine.

## Architecture Rule

Python core calculates.  
SQLite stores.  
Reports explain.  
Hermes or any AI agent may orchestrate later.

The Python core must work without Hermes or any AI agent.

## What Agents May Do

Agents may:
- write and refactor code
- add tests
- run tests
- improve documentation
- add deterministic strategies
- improve error handling
- improve reports
- create CLI commands
- inspect generated JSON/Markdown reports
- add read-only broker data ingestion for market data, ledger, holdings, positions, and trade history

## What Agents Must Not Do

Agents must not:
- invent market prices
- call a setup a guaranteed trade
- use "buy now" or "sell now" language
- add broker execution without explicit instruction
- add broker order placement, order modification, order cancellation, or auto execution
- add OpenAlgo dependency
- commit secrets
- hardcode API keys
- bypass risk rules
- edit the SQLite database directly outside repository/database abstractions
- create paid signal or advisory features

## Language Rules

Use:
- setup detected
- watchlist candidate
- risk check passed
- risk check failed
- entry trigger pending
- self-directed analysis

Avoid:
- buy now
- strong buy
- guaranteed target
- sure shot
- high conviction call
- AI recommendation

## v0.1 Scope

Build only:
- Python core
- strategy engine
- scanner engine
- SQLite database
- risk engine
- backtesting scaffold
- CLI
- JSON/Markdown reports
- tests
- Hermes-friendly shell script
- optional read-only broker data ingestion

Do not build:
- web app
- desktop app
- mobile app
- broker execution connector
- Telegram bot
- AI connector
- auto execution

## Testing Requirement

Before completing work, run:

```bash
python -m compileall arthavyuh
pytest
arthavyuh health
arthavyuh scan --all --watchlist config/watchlists/sample_watchlist.csv
arthavyuh report evening
```

Fix failures before final response.
