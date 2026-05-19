from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    country: str
    climate_label: str
    latitude: float
    longitude: float
    elevation_m: float | None
    timezone: str
    dwd_station_id: str | None = None
    noaa_station_id: str | None = None
    nasa_enabled: bool = False


@dataclass(frozen=True)
class Observation:
    source: str
    location_id: str
    timestamp_utc: str
    timestamp_local: str
    year: int
    month: int
    hour_local: int
    dry_bulb_c: float | None
    wet_bulb_c: float | None
    dew_point_c: float | None
    relative_humidity_pct: float | None
    pressure_hpa: float | None
    wind_speed_ms: float | None
    quality_code: str | None
    valid: bool
    raw_payload: str | None = None

