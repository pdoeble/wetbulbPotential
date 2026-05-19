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
    site_id: str | None = None
    site_type: str | None = None
    region: str | None = None
    climate_tags: tuple[str, ...] = ()
    priority: int | None = None
    primary_source: str | None = None
    secondary_source: str | None = None
    primary_access_url: str | None = None
    station_candidate_name: str | None = None
    station_candidate_id: str | None = None
    station_candidate_distance_km: float | None = None
    wetbulb_method: str | None = None
    data_start: str | None = None
    data_end: str | None = None
    availability_score: float | None = None
    notes: str | None = None


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
    solar_radiation_w_m2: float | None
    quality_code: str | None
    valid: bool
    raw_payload: str | None = None
