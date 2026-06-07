"""JSON report writer."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from arthavyuh.core.config import DEFAULT_DAILY_REPORTS_DIR, resolve_path


def write_json_report(
    payload: dict[str, Any],
    reports_dir: str | Path = DEFAULT_DAILY_REPORTS_DIR,
    report_date: str | None = None,
) -> Path:
    resolved_dir = resolve_path(reports_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)
    date_part = report_date or payload.get("report_date")
    if not date_part:
        raise ValueError("report_date is required for JSON report output")

    output_path = resolved_dir / f"signals_{date_part}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    shutil.copyfile(output_path, resolved_dir / "latest.json")
    return output_path
