from pathlib import Path

from arthavyuh.reports.evening_report import generate_evening_report
from arthavyuh.reports.markdown import DISCLAIMER
from arthavyuh.scanners.scanner import run_scan


def test_evening_report_generation(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    db_path = tmp_path / "arthavyuh.db"
    scan_payload = run_scan(
        run_all=True,
        db_path=db_path,
        reports_dir=reports_dir,
        report_date="2026-06-07",
    )

    report = generate_evening_report(
        payload=scan_payload,
        reports_dir=reports_dir,
        db_path=db_path,
    )

    latest = reports_dir / "latest.md"
    assert report["status"] == "PASS"
    assert latest.exists()
    assert DISCLAIMER in latest.read_text(encoding="utf-8")
