from __future__ import annotations

import sqlite3
from pathlib import Path

from wetbulb_pipeline.importers import noaa
from wetbulb_pipeline.sync import _export_years, _restart_args_for_command, update_all


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


def test_update_skips_noaa_year_when_remote_file_is_missing(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "stations.yml"
    raw_db = tmp_path / "raw.sqlite"
    config_path.write_text(
        """
defaults:
  year_start: 2002
  year_end: 2002
locations:
  - id: missing-noaa
    name: Missing NOAA
    country: US
    climate_label: test
    latitude: 38.0
    longitude: -122.0
    elevation_m: 10
    timezone: America/Los_Angeles
    noaa:
      station_id: "00000099999"
""",
        encoding="utf-8",
    )

    def missing_download(
        station_id: str,
        year: int,
        destination_dir: str | Path,
        reporthook=None,
    ) -> None:
        marker = noaa.missing_marker_path(station_id, year, destination_dir)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("404 Not Found\n", encoding="utf-8")
        return None

    monkeypatch.setattr(noaa, "download_year", missing_download)

    results = update_all(
        config_path,
        raw_db,
        years=(2002, 2002),
        sources=["noaa"],
        export_after=False,
        dry_run=False,
    )

    assert results[0].skipped is True
    assert results[0].input_ref.startswith("missing:")
    with sqlite3.connect(raw_db) as conn:
        observation_count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    assert observation_count == 0


def test_update_reports_progress_when_callback_is_provided(tmp_path: Path) -> None:
    config_path = tmp_path / "stations.yml"
    raw_db = tmp_path / "raw.sqlite"
    config_path.write_text(
        """
defaults:
  year_start: 2002
  year_end: 2002
locations:
  - id: dry-run-noaa
    name: Dry Run NOAA
    country: US
    climate_label: test
    latitude: 38.0
    longitude: -122.0
    elevation_m: 10
    timezone: America/Los_Angeles
    noaa:
      station_id: "PROGRESS_TEST_STATION"
""",
        encoding="utf-8",
    )
    messages: list[str] = []

    update_all(
        config_path,
        raw_db,
        years=(2002, 2002),
        sources=["noaa"],
        export_after=False,
        dry_run=True,
        progress=messages.append,
    )

    assert any("Starting update" in message for message in messages)
    assert any("[0001/0001] NOAA dry-run-noaa" in message for message in messages)
    assert any("dry-run would import" in message for message in messages)


def test_update_export_years_keep_project_start() -> None:
    assert _export_years({"defaults": {"year_start": 2002}}, (2013, 2025)) == (2002, 2025)


def test_restart_args_are_recreated_for_local_servers() -> None:
    dash_args = _restart_args_for_command(
        "python -m wetbulb_pipeline dash --data web/public/data --port 8050",
        8050,
    )
    static_args = _restart_args_for_command(
        "python -m http.server 8060 --directory site",
        8060,
    )

    assert dash_args is not None
    assert dash_args[1:] == (
        "-m",
        "wetbulb_pipeline",
        "dash",
        "--data",
        "web/public/data",
        "--port",
        "8050",
    )
    assert static_args is not None
    assert static_args[1:] == ("-m", "http.server", "8060", "--directory", "site")
