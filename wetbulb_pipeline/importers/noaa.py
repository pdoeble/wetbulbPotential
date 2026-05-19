from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlretrieve
from zoneinfo import ZoneInfo

from wetbulb_pipeline.models import Location, Observation
from wetbulb_pipeline.psychrometrics import (
    relative_humidity_from_dewpoint,
    station_pressure_from_sea_level_hpa,
    wet_bulb_c,
)

SOURCE = "NOAA"
BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"


def download_year(station_id: str, year: int, destination_dir: str | Path) -> Path:
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"{station_id}_{year}.csv"
    if target.exists() and target.stat().st_size > 0:
        return target
    urlretrieve(f"{BASE_URL}/{year}/{station_id}.csv", target)
    return target


def _parse_scaled_field(
    value: str | None, missing: int, scale: float = 10.0
) -> tuple[float | None, str]:
    if not value:
        return None, ""
    parts = [part.strip() for part in value.split(",")]
    raw = parts[0] if parts else ""
    quality = parts[1] if len(parts) > 1 else ""
    try:
        numeric = int(raw)
    except ValueError:
        return None, quality
    if abs(numeric) == missing:
        return None, quality
    return numeric / scale, quality


def _parse_wind_ms(value: str | None) -> tuple[float | None, str]:
    if not value:
        return None, ""
    parts = [part.strip() for part in value.split(",")]
    quality = parts[1] if len(parts) > 1 else ""
    try:
        speed = int(parts[3])
    except (IndexError, ValueError):
        return None, quality
    if speed == 9999:
        return None, quality
    return speed / 10.0, quality


def _valid_quality(*flags: str) -> bool:
    bad_flags = {"2", "3", "6", "7"}
    return not any(flag in bad_flags for flag in flags if flag)


def read_observations(path: str | Path, location: Location) -> list[Observation]:
    observations: list[Observation] = []
    timezone = ZoneInfo(location.timezone)
    with Path(path).open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp_utc_dt = datetime.fromisoformat(row["DATE"].replace("Z", "+00:00"))
            if timestamp_utc_dt.tzinfo is None:
                timestamp_utc_dt = timestamp_utc_dt.replace(tzinfo=UTC)
            timestamp_utc_dt = timestamp_utc_dt.astimezone(UTC)
            timestamp_local_dt = timestamp_utc_dt.astimezone(timezone)

            dry, dry_q = _parse_scaled_field(row.get("TMP"), 9999)
            dew, dew_q = _parse_scaled_field(row.get("DEW"), 9999)
            slp, slp_q = _parse_scaled_field(row.get("SLP"), 99999)
            wind, wind_q = _parse_wind_ms(row.get("WND"))
            pressure = (
                station_pressure_from_sea_level_hpa(slp, location.elevation_m, dry)
                if slp is not None
                else None
            )
            wet = wet_bulb_c(dry, dew, pressure) if dry is not None and dew is not None else None
            rh = (
                relative_humidity_from_dewpoint(dry, dew)
                if dry is not None and dew is not None
                else None
            )
            valid = (
                dry is not None
                and dew is not None
                and wet is not None
                and _valid_quality(dry_q, dew_q)
            )
            observations.append(
                Observation(
                    source=SOURCE,
                    location_id=location.id,
                    timestamp_utc=timestamp_utc_dt.isoformat().replace("+00:00", "Z"),
                    timestamp_local=timestamp_local_dt.replace(tzinfo=None).isoformat(),
                    year=timestamp_local_dt.year,
                    month=timestamp_local_dt.month,
                    hour_local=timestamp_local_dt.hour,
                    dry_bulb_c=dry,
                    wet_bulb_c=wet,
                    dew_point_c=dew,
                    relative_humidity_pct=rh,
                    pressure_hpa=pressure,
                    wind_speed_ms=wind,
                    quality_code=json.dumps(
                        {
                            "record": row.get("QUALITY_CONTROL"),
                            "tmp": dry_q,
                            "dew": dew_q,
                            "slp": slp_q,
                            "wind": wind_q,
                        },
                        separators=(",", ":"),
                    ),
                    valid=valid,
                    raw_payload=json.dumps(
                        {"report_type": row.get("REPORT_TYPE"), "station": row.get("STATION")},
                        separators=(",", ":"),
                    ),
                )
            )
    return observations
