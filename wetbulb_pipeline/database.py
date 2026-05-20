from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from .models import Location, Observation

RAW_SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS locations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  climate_label TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  elevation_m REAL,
  timezone TEXT NOT NULL,
  dwd_station_id TEXT,
  noaa_station_id TEXT,
  nasa_enabled INTEGER NOT NULL DEFAULT 0,
  site_id TEXT,
  site_type TEXT,
  region TEXT,
  climate_tags TEXT,
  priority INTEGER,
  primary_source TEXT,
  secondary_source TEXT,
  primary_access_url TEXT,
  station_candidate_name TEXT,
  station_candidate_id TEXT,
  station_candidate_distance_km REAL,
  wetbulb_method TEXT,
  data_start TEXT,
  data_end TEXT,
  availability_score REAL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS import_batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  location_id TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  input_ref TEXT NOT NULL,
  note TEXT
);

CREATE TABLE IF NOT EXISTS observations (
  source TEXT NOT NULL,
  location_id TEXT NOT NULL,
  timestamp_utc TEXT NOT NULL,
  timestamp_local TEXT NOT NULL,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  hour_local INTEGER NOT NULL,
  dry_bulb_c REAL,
  wet_bulb_c REAL,
  dew_point_c REAL,
  relative_humidity_pct REAL,
  pressure_hpa REAL,
  wind_speed_ms REAL,
  solar_radiation_w_m2 REAL,
  quality_code TEXT,
  valid INTEGER NOT NULL,
  raw_payload TEXT,
  import_batch_id INTEGER,
  PRIMARY KEY (source, location_id, timestamp_utc),
  FOREIGN KEY (location_id) REFERENCES locations(id),
  FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
);

CREATE INDEX IF NOT EXISTS idx_observations_filter
ON observations (source, location_id, year, month, hour_local, valid);
"""


PROCESSED_SCHEMA = """
CREATE TABLE locations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  climate_label TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  elevation_m REAL,
  timezone TEXT NOT NULL,
  dwd_station_id TEXT,
  noaa_station_id TEXT,
  nasa_enabled INTEGER NOT NULL DEFAULT 0,
  site_id TEXT,
  site_type TEXT,
  region TEXT,
  climate_tags TEXT,
  priority INTEGER,
  primary_source TEXT,
  secondary_source TEXT,
  primary_access_url TEXT,
  station_candidate_name TEXT,
  station_candidate_id TEXT,
  station_candidate_distance_km REAL,
  wetbulb_method TEXT,
  data_start TEXT,
  data_end TEXT,
  availability_score REAL,
  notes TEXT
);

CREATE TABLE aggregates (
  source TEXT NOT NULL,
  location_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  hour_local INTEGER NOT NULL,
  count INTEGER NOT NULL,
  mean REAL NOT NULL,
  min REAL NOT NULL,
  max REAL NOT NULL,
  PRIMARY KEY (source, location_id, metric, year, month, hour_local)
);
"""

LOCATION_EXTRA_COLUMNS = {
    "site_id": "TEXT",
    "site_type": "TEXT",
    "region": "TEXT",
    "climate_tags": "TEXT",
    "priority": "INTEGER",
    "primary_source": "TEXT",
    "secondary_source": "TEXT",
    "primary_access_url": "TEXT",
    "station_candidate_name": "TEXT",
    "station_candidate_id": "TEXT",
    "station_candidate_distance_km": "REAL",
    "wetbulb_method": "TEXT",
    "data_start": "TEXT",
    "data_end": "TEXT",
    "availability_score": "REAL",
    "notes": "TEXT",
}

OBSERVATION_EXTRA_COLUMNS = {
    "solar_radiation_w_m2": "REAL",
}


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_raw_db(path: str | Path) -> None:
    with connect(path) as conn:
        conn.executescript(RAW_SCHEMA)
        _ensure_columns(conn, "locations", LOCATION_EXTRA_COLUMNS)
        _ensure_columns(conn, "observations", OBSERVATION_EXTRA_COLUMNS)


def upsert_locations(conn: sqlite3.Connection, locations: Iterable[Location]) -> None:
    conn.executemany(
        """
        INSERT INTO locations (
          id, name, country, climate_label, latitude, longitude, elevation_m, timezone,
          dwd_station_id, noaa_station_id, nasa_enabled, site_id, site_type, region,
          climate_tags, priority, primary_source, secondary_source, primary_access_url,
          station_candidate_name, station_candidate_id, station_candidate_distance_km,
          wetbulb_method, data_start, data_end, availability_score, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name = excluded.name,
          country = excluded.country,
          climate_label = excluded.climate_label,
          latitude = excluded.latitude,
          longitude = excluded.longitude,
          elevation_m = excluded.elevation_m,
          timezone = excluded.timezone,
          dwd_station_id = excluded.dwd_station_id,
          noaa_station_id = excluded.noaa_station_id,
          nasa_enabled = excluded.nasa_enabled,
          site_id = excluded.site_id,
          site_type = excluded.site_type,
          region = excluded.region,
          climate_tags = excluded.climate_tags,
          priority = excluded.priority,
          primary_source = excluded.primary_source,
          secondary_source = excluded.secondary_source,
          primary_access_url = excluded.primary_access_url,
          station_candidate_name = excluded.station_candidate_name,
          station_candidate_id = excluded.station_candidate_id,
          station_candidate_distance_km = excluded.station_candidate_distance_km,
          wetbulb_method = excluded.wetbulb_method,
          data_start = excluded.data_start,
          data_end = excluded.data_end,
          availability_score = excluded.availability_score,
          notes = excluded.notes
        """,
        [
            (
                location.id,
                location.name,
                location.country,
                location.climate_label,
                location.latitude,
                location.longitude,
                location.elevation_m,
                location.timezone,
                location.dwd_station_id,
                location.noaa_station_id,
                int(location.nasa_enabled),
                location.site_id,
                location.site_type,
                location.region,
                ",".join(location.climate_tags),
                location.priority,
                location.primary_source,
                location.secondary_source,
                location.primary_access_url,
                location.station_candidate_name,
                location.station_candidate_id,
                location.station_candidate_distance_km,
                location.wetbulb_method,
                location.data_start,
                location.data_end,
                location.availability_score,
                location.notes,
            )
            for location in locations
        ],
    )


def create_import_batch(
    conn: sqlite3.Connection, source: str, location_id: str, input_ref: str, note: str | None = None
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO import_batches (source, location_id, input_ref, note)
        VALUES (?, ?, ?, ?)
        """,
        (source, location_id, input_ref, note),
    )
    return int(cursor.lastrowid)


def upsert_observations(
    conn: sqlite3.Connection, observations: Iterable[Observation], import_batch_id: int
) -> int:
    rows = [
        (
            obs.source,
            obs.location_id,
            obs.timestamp_utc,
            obs.timestamp_local,
            obs.year,
            obs.month,
            obs.hour_local,
            obs.dry_bulb_c,
            obs.wet_bulb_c,
            obs.dew_point_c,
            obs.relative_humidity_pct,
            obs.pressure_hpa,
            obs.wind_speed_ms,
            obs.solar_radiation_w_m2,
            obs.quality_code,
            int(obs.valid),
            obs.raw_payload,
            import_batch_id,
        )
        for obs in observations
    ]
    conn.executemany(
        """
        INSERT INTO observations (
          source, location_id, timestamp_utc, timestamp_local, year, month, hour_local,
          dry_bulb_c, wet_bulb_c, dew_point_c, relative_humidity_pct, pressure_hpa,
          wind_speed_ms, solar_radiation_w_m2, quality_code, valid, raw_payload,
          import_batch_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, location_id, timestamp_utc) DO UPDATE SET
          timestamp_local = excluded.timestamp_local,
          year = excluded.year,
          month = excluded.month,
          hour_local = excluded.hour_local,
          dry_bulb_c = excluded.dry_bulb_c,
          wet_bulb_c = excluded.wet_bulb_c,
          dew_point_c = excluded.dew_point_c,
          relative_humidity_pct = excluded.relative_humidity_pct,
          pressure_hpa = excluded.pressure_hpa,
          wind_speed_ms = excluded.wind_speed_ms,
          solar_radiation_w_m2 = excluded.solar_radiation_w_m2,
          quality_code = excluded.quality_code,
          valid = excluded.valid,
          raw_payload = excluded.raw_payload,
          import_batch_id = excluded.import_batch_id
        """,
        rows,
    )
    return len(rows)


def _ensure_columns(
    conn: sqlite3.Connection, table_name: str, columns: dict[str, str]
) -> None:
    existing = {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")}
    for column_name, column_type in columns.items():
        if column_name not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
