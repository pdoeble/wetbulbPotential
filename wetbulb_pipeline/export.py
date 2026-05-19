from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .database import PROCESSED_SCHEMA, connect

METRICS = {
    "delta_t_k": {
        "label": "Delta T dry bulb - wet bulb",
        "unit": "K",
        "expression": "dry_bulb_c - wet_bulb_c",
    },
    "dry_bulb_c": {
        "label": "Dry bulb temperature",
        "unit": "degC",
        "expression": "dry_bulb_c",
    },
    "wet_bulb_c": {
        "label": "Wet bulb temperature",
        "unit": "degC",
        "expression": "wet_bulb_c",
    },
    "relative_humidity_pct": {
        "label": "Relative humidity",
        "unit": "%",
        "expression": "relative_humidity_pct",
    },
    "pressure_hpa": {
        "label": "Pressure",
        "unit": "hPa",
        "expression": "pressure_hpa",
    },
}


def export_processed(
    raw_db: str | Path,
    processed_db: str | Path = "web/public/data/wetbulb_processed.sqlite",
    manifest_path: str | Path = "web/public/data/manifest.json",
    max_bytes: int = 100 * 1024 * 1024,
) -> None:
    processed_path = Path(processed_db)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    if processed_path.exists():
        processed_path.unlink()

    with connect(raw_db) as raw, sqlite3.connect(processed_path) as processed:
        processed.row_factory = sqlite3.Row
        processed.executescript(PROCESSED_SCHEMA)
        processed.executemany(
            """
            INSERT INTO locations (
              id, name, country, climate_label, latitude, longitude, elevation_m,
              timezone, dwd_station_id, noaa_station_id, nasa_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            raw.execute(
                """
                SELECT id, name, country, climate_label, latitude, longitude, elevation_m,
                       timezone, dwd_station_id, noaa_station_id, nasa_enabled
                FROM locations
                WHERE id IN (SELECT DISTINCT location_id FROM observations WHERE valid = 1)
                """
            ).fetchall(),
        )
        for metric, info in METRICS.items():
            expression = info["expression"]
            processed.executemany(
                """
                INSERT INTO aggregates (
                  source, location_id, metric, year, month, hour_local, count, mean, min, max
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                raw.execute(
                    f"""
                    SELECT
                      source,
                      location_id,
                      ? AS metric,
                      year,
                      month,
                      hour_local,
                      COUNT({expression}) AS count,
                      AVG({expression}) AS mean,
                      MIN({expression}) AS min,
                      MAX({expression}) AS max
                    FROM observations
                    WHERE valid = 1
                      AND {expression} IS NOT NULL
                    GROUP BY source, location_id, year, month, hour_local
                    """,
                    (metric,),
                ).fetchall(),
            )
        processed.commit()

    size = processed_path.stat().st_size
    if size > max_bytes:
        table_sizes = _estimate_table_sizes(processed_path)
        processed_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Processed database exceeds {max_bytes} bytes ({size} bytes). "
            f"Largest tables: {table_sizes}"
        )

    manifest = build_manifest(processed_path, size)
    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_manifest(processed_db: str | Path, db_size_bytes: int | None = None) -> dict:
    db_path = Path(processed_db)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        locations = [dict(row) for row in conn.execute("SELECT * FROM locations ORDER BY name")]
        availability = [
            dict(row)
            for row in conn.execute(
                """
                SELECT source, location_id, metric, MIN(year) AS year_min, MAX(year) AS year_max,
                       COUNT(*) AS cells
                FROM aggregates
                GROUP BY source, location_id, metric
                ORDER BY source, location_id, metric
                """
            )
        ]
    return {
        "version": 1,
        "generated_from": "wetbulb_pipeline",
        "database": {
            "path": "data/wetbulb_processed.sqlite",
            "size_bytes": db_size_bytes if db_size_bytes is not None else os.path.getsize(db_path),
        },
        "locations": locations,
        "availability": availability,
        "metrics": [
            {"id": metric, "label": info["label"], "unit": info["unit"]}
            for metric, info in METRICS.items()
        ],
        "plot_types": [
            {"id": "heatmap", "label": "Heatmap"},
            {"id": "contour", "label": "Isolines"},
            {"id": "combined", "label": "Heatmap + isolines"},
        ],
        "sources": [
            {
                "id": "DWD",
                "label": "Deutscher Wetterdienst hourly moisture",
                "url": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/moisture/",
                "license": "CC BY 4.0",
            },
            {
                "id": "NOAA",
                "label": "NOAA NCEI Global Hourly / ISD",
                "url": "https://www.ncei.noaa.gov/data/global-hourly/access/",
                "license": "NOAA open data",
            },
            {
                "id": "NASA_POWER",
                "label": "NASA POWER Hourly API",
                "url": "https://power.larc.nasa.gov/docs/services/api/temporal/hourly/",
                "license": "NASA POWER",
            },
        ],
    }


def _estimate_table_sizes(path: Path) -> list[tuple[str, int]]:
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """
            SELECT name, COUNT(*) AS rows
            FROM sqlite_master
            WHERE type = 'table'
            GROUP BY name
            """
        ).fetchall()
    return [(str(row[0]), int(row[1])) for row in rows]

