from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

from wetbulb_pipeline.config import get_location, load_locations
from wetbulb_pipeline.database import (
    connect,
    create_import_batch,
    init_raw_db,
    upsert_locations,
    upsert_observations,
)
from wetbulb_pipeline.export import export_processed
from wetbulb_pipeline.importers.dwd import read_observations


def test_import_is_idempotent_and_export_writes_manifest(tmp_path: Path) -> None:
    raw_db = tmp_path / "raw.sqlite"
    processed_db = tmp_path / "processed.sqlite"
    manifest_path = tmp_path / "manifest.json"
    location = get_location("stuttgart-neckartal")
    observations = read_observations(
        "produkt_tf_stunde_20021101_20130514_04926.txt",
        location,
    )[:24]

    init_raw_db(raw_db)
    with connect(raw_db) as conn:
        upsert_locations(conn, load_locations())
        first_batch = create_import_batch(conn, "DWD", location.id, "fixture")
        second_batch = create_import_batch(conn, "DWD", location.id, "fixture")
        upsert_observations(conn, observations, first_batch)
        upsert_observations(conn, observations, second_batch)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]

    assert count == len(observations)

    export_processed(raw_db, processed_db, manifest_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["database"]["path"] == "data/wetbulb_processed.sqlite"
    assert any(location["id"] == "stuttgart-neckartal" for location in manifest["locations"])
    assert [metric["id"] for metric in manifest["metrics"]] == ["delta_t_k"]

    with sqlite3.connect(processed_db) as conn:
        aggregate_count = conn.execute("SELECT COUNT(*) FROM aggregates").fetchone()[0]
        exported_metrics = [
            row[0] for row in conn.execute("SELECT DISTINCT metric FROM aggregates ORDER BY metric")
        ]
    assert aggregate_count > 0
    assert exported_metrics == ["delta_t_k"]


def test_export_can_include_all_metrics_for_local_analysis(tmp_path: Path) -> None:
    raw_db = tmp_path / "raw.sqlite"
    processed_db = tmp_path / "processed.sqlite"
    manifest_path = tmp_path / "manifest.json"
    location = get_location("stuttgart-neckartal")
    observations = read_observations("produkt_tf_stunde_20021101_20130514_04926.txt", location)[:24]

    init_raw_db(raw_db)
    with connect(raw_db) as conn:
        upsert_locations(conn, load_locations())
        batch = create_import_batch(conn, "DWD", location.id, "fixture")
        upsert_observations(conn, observations, batch)
        conn.commit()

    export_processed(
        raw_db,
        processed_db,
        manifest_path,
        metrics=["delta_t_k", "dry_bulb_c", "wet_bulb_c"],
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [metric["id"] for metric in manifest["metrics"]] == [
        "delta_t_k",
        "dry_bulb_c",
        "wet_bulb_c",
    ]


def test_export_can_filter_local_year_range(tmp_path: Path) -> None:
    raw_db = tmp_path / "raw.sqlite"
    processed_db = tmp_path / "processed.sqlite"
    manifest_path = tmp_path / "manifest.json"
    location = get_location("stuttgart-neckartal")
    observations = read_observations("produkt_tf_stunde_20021101_20130514_04926.txt", location)[:24]
    future_observation = replace(
        observations[0],
        timestamp_utc="2026-01-01T00:00:00+00:00",
        timestamp_local="2026-01-01T01:00:00+01:00",
        year=2026,
        month=1,
        hour_local=1,
    )

    init_raw_db(raw_db)
    with connect(raw_db) as conn:
        upsert_locations(conn, load_locations())
        batch = create_import_batch(conn, "DWD", location.id, "fixture")
        upsert_observations(conn, [*observations, future_observation], batch)
        conn.commit()

    export_processed(raw_db, processed_db, manifest_path, years=(2002, 2025))

    with sqlite3.connect(processed_db) as conn:
        min_year, max_year = conn.execute("SELECT MIN(year), MAX(year) FROM aggregates").fetchone()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert min_year == 2002
    assert max_year == 2002
    assert manifest["availability"][0]["year_min"] == 2002
    assert manifest["availability"][0]["year_max"] == 2002
