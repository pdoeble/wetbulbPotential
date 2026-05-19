from __future__ import annotations

import json
import sqlite3
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
    observations = read_observations("produkt_tf_stunde_20021101_20130514_04926.txt", location)[:24]

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

    with sqlite3.connect(processed_db) as conn:
        aggregate_count = conn.execute("SELECT COUNT(*) FROM aggregates").fetchone()[0]
    assert aggregate_count > 0
