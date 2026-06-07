from pathlib import Path

from arthavyuh.scanners.scanner import run_scan


def test_scanner_runs_on_sample_watchlist(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    payload = run_scan(
        run_all=True,
        db_path=tmp_path / "arthavyuh.db",
        reports_dir=reports_dir,
        report_date="2026-06-07",
    )

    assert payload["summary"]["total_symbols_scanned"] == 3
    assert payload["summary"]["total_strategies_run"] == 9
    assert payload["summary"]["signals_generated"] > 0
    assert (reports_dir / "latest.json").exists()
