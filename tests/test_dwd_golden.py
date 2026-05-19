from __future__ import annotations

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


def test_dwd_stuttgart_golden_heatmap_values(tmp_path: Path) -> None:
    raw_db = tmp_path / "raw.sqlite"
    processed_db = tmp_path / "processed.sqlite"
    manifest = tmp_path / "manifest.json"
    location = get_location("stuttgart-neckartal")

    init_raw_db(raw_db)
    with connect(raw_db) as conn:
        upsert_locations(conn, load_locations())
        observations = read_observations("produkt_tf_stunde_20021101_20130514_04926.txt", location)
        batch_id = create_import_batch(conn, "DWD", location.id, "fixture")
        upsert_observations(conn, observations, batch_id)
        conn.commit()

    export_processed(raw_db, processed_db, manifest)

    with sqlite3.connect(processed_db) as conn:
        july_15 = conn.execute(
            """
            SELECT SUM(mean * count) / SUM(count)
            FROM aggregates
            WHERE source = 'DWD'
              AND location_id = 'stuttgart-neckartal'
              AND metric = 'delta_t_k'
              AND month = 7
              AND hour_local = 15
            """
        ).fetchone()[0]
        december_04 = conn.execute(
            """
            SELECT SUM(mean * count) / SUM(count)
            FROM aggregates
            WHERE source = 'DWD'
              AND location_id = 'stuttgart-neckartal'
              AND metric = 'delta_t_k'
              AND month = 12
              AND hour_local = 4
            """
        ).fetchone()[0]
        cells = conn.execute(
            """
            SELECT COUNT(DISTINCT month || '-' || hour_local)
            FROM aggregates
            WHERE source = 'DWD'
              AND location_id = 'stuttgart-neckartal'
              AND metric = 'delta_t_k'
            """
        ).fetchone()[0]

    assert round(july_15, 2) == 8.19
    assert round(december_04, 2) == 1.08
    assert cells == 288

