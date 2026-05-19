from __future__ import annotations

import sqlite3
from pathlib import Path

from wetbulb_pipeline.sync import update_all


def test_update_dry_run_plans_missing_years_without_importing(tmp_path: Path) -> None:
    raw_db = tmp_path / "raw.sqlite"

    results = update_all(
        "configs/stations.yml",
        raw_db,
        years=(2002, 2002),
        sources=["noaa"],
        export_after=False,
        dry_run=True,
    )

    assert any(result.source == "NOAA" and result.skipped is False for result in results)
    with sqlite3.connect(raw_db) as conn:
        observation_count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    assert observation_count == 0

