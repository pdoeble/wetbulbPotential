from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .database import PROCESSED_SCHEMA, connect, init_raw_db

DEFAULT_EXPORT_METRICS = ("delta_t_k",)

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
    "solar_radiation_w_m2": {
        "label": "Solar radiation",
        "unit": "W/m2",
        "expression": "solar_radiation_w_m2",
    },
}

LOCATION_COLUMNS = [
    "id",
    "name",
    "country",
    "climate_label",
    "latitude",
    "longitude",
    "elevation_m",
    "timezone",
    "dwd_station_id",
    "noaa_station_id",
    "nasa_enabled",
    "site_id",
    "site_type",
    "region",
    "climate_tags",
    "priority",
    "primary_source",
    "secondary_source",
    "primary_access_url",
    "station_candidate_name",
    "station_candidate_id",
    "station_candidate_distance_km",
    "wetbulb_method",
    "data_start",
    "data_end",
    "availability_score",
    "notes",
]


def export_processed(
    raw_db: str | Path,
    processed_db: str | Path = "web/public/data/wetbulb_processed.sqlite",
    manifest_path: str | Path = "web/public/data/manifest.json",
    max_bytes: int = 100 * 1024 * 1024,
    metrics: list[str] | tuple[str, ...] | None = DEFAULT_EXPORT_METRICS,
) -> None:
    selected_metrics = _selected_metrics(metrics)
    processed_path = Path(processed_db)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = processed_path.with_name(f"{processed_path.name}.tmp")
    if temp_path.exists():
        temp_path.unlink()

    init_raw_db(raw_db)
    raw = connect(raw_db)
    processed = sqlite3.connect(temp_path)
    try:
        processed.row_factory = sqlite3.Row
        processed.executescript(PROCESSED_SCHEMA)
        location_columns = ", ".join(LOCATION_COLUMNS)
        location_placeholders = ", ".join("?" for _ in LOCATION_COLUMNS)
        processed.executemany(
            f"INSERT INTO locations ({location_columns}) VALUES ({location_placeholders})",
            raw.execute(
                f"""
                SELECT {location_columns}
                FROM locations
                WHERE id IN (SELECT DISTINCT location_id FROM observations WHERE valid = 1)
                """
            ).fetchall(),
        )
        for metric in selected_metrics:
            info = METRICS[metric]
            processed.executemany(
                """
                INSERT INTO aggregates (
                  source, location_id, metric, year, month, hour_local, count,
                  mean, min, max
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
                      COUNT({info["expression"]}) AS count,
                      AVG({info["expression"]}) AS mean,
                      MIN({info["expression"]}) AS min,
                      MAX({info["expression"]}) AS max
                    FROM observations
                    WHERE valid = 1
                      AND {info["expression"]} IS NOT NULL
                    GROUP BY source, location_id, year, month, hour_local
                    """,
                    (metric,),
                ).fetchall(),
            )
        processed.commit()
    finally:
        processed.close()
        raw.close()

    size = temp_path.stat().st_size
    if size > max_bytes:
        table_sizes = _estimate_table_sizes(temp_path)
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Processed database exceeds {max_bytes} bytes ({size} bytes). "
            f"Largest tables: {table_sizes}"
        )

    manifest = build_manifest(temp_path, size, selected_metrics)
    try:
        os.replace(temp_path, processed_path)
    except PermissionError as exc:
        raise RuntimeError(
            f"Cannot replace processed database {processed_path}; it is locked by "
            "another process. Close local Dash/static servers or SQLite viewers that "
            "use this file, then rerun `python -m wetbulb_pipeline export`."
        ) from exc

    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_manifest(
    processed_db: str | Path,
    db_size_bytes: int | None = None,
    metrics: list[str] | tuple[str, ...] | None = None,
) -> dict:
    db_path = Path(processed_db)
    conn = sqlite3.connect(db_path)
    try:
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
    finally:
        conn.close()
    selected_metrics = _selected_metrics(metrics or [item["metric"] for item in availability])
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
            for metric in selected_metrics
            for info in [METRICS[metric]]
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


def _selected_metrics(metrics: list[str] | tuple[str, ...] | None) -> list[str]:
    requested = list(metrics or DEFAULT_EXPORT_METRICS)
    unknown = [metric for metric in requested if metric not in METRICS]
    if unknown:
        raise ValueError(f"Unknown export metric(s): {', '.join(unknown)}")
    return [metric for metric in METRICS if metric in set(requested)]


def _estimate_table_sizes(path: Path) -> list[tuple[str, int]]:
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            """
            SELECT name, COUNT(*) AS rows
            FROM sqlite_master
            WHERE type = 'table'
            GROUP BY name
            """
        ).fetchall()
    finally:
        conn.close()
    return [(str(row[0]), int(row[1])) for row in rows]
