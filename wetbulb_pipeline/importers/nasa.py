from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlretrieve
from zoneinfo import ZoneInfo

from wetbulb_pipeline.models import Location, Observation

SOURCE = "NASA_POWER"
BASE_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMETERS = "T2M,T2MWET,T2MDEW,RH2M,PS,WS10M,ALLSKY_SFC_SW_DWN"


def build_power_url(
    latitude: float,
    longitude: float,
    start: str = "20020101",
    end: str = "20131231",
    time_standard: str = "UTC",
) -> str:
    query = urlencode(
        {
            "parameters": PARAMETERS,
            "community": "SB",
            "longitude": longitude,
            "latitude": latitude,
            "start": start,
            "end": end,
            "format": "CSV",
            "time-standard": time_standard,
        }
    )
    return f"{BASE_URL}?{query}"


def download_range(
    location: Location,
    start: str,
    end: str,
    destination_dir: str | Path,
    time_standard: str = "UTC",
) -> Path:
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"{location.id}_{start}_{end}_{time_standard}.csv"
    if target.exists() and target.stat().st_size > 0:
        return target
    urlretrieve(
        build_power_url(location.latitude, location.longitude, start, end, time_standard),
        target,
    )
    return target


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    parsed = float(value)
    if parsed == -999:
        return None
    return parsed


def read_observations(
    path: str | Path, location: Location, time_standard: str = "UTC"
) -> list[Observation]:
    csv_lines: list[str] = []
    in_data = False
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if in_data:
                csv_lines.append(line)
            elif line.strip() == "-END HEADER-":
                in_data = True

    timezone = ZoneInfo(location.timezone)
    observations: list[Observation] = []
    reader = csv.DictReader(csv_lines)
    for row in reader:
        timestamp = datetime(
            int(row["YEAR"]), int(row["MO"]), int(row["DY"]), int(row["HR"])
        )
        if time_standard.upper() == "UTC":
            timestamp_utc_dt = timestamp.replace(tzinfo=UTC)
            timestamp_local_dt = timestamp_utc_dt.astimezone(timezone)
        else:
            timestamp_local_dt = timestamp.replace(tzinfo=timezone)
            timestamp_utc_dt = timestamp_local_dt.astimezone(UTC)
        dry = _parse_float(row.get("T2M"))
        wet = _parse_float(row.get("T2MWET"))
        dew = _parse_float(row.get("T2MDEW"))
        rh = _parse_float(row.get("RH2M"))
        pressure_kpa = _parse_float(row.get("PS"))
        pressure_hpa = pressure_kpa * 10.0 if pressure_kpa is not None else None
        wind = _parse_float(row.get("WS10M"))
        solar = _parse_float(row.get("ALLSKY_SFC_SW_DWN"))
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
                pressure_hpa=pressure_hpa,
                wind_speed_ms=wind,
                solar_radiation_w_m2=solar,
                quality_code=time_standard.upper(),
                valid=dry is not None and wet is not None,
                raw_payload=json.dumps({"source": "NASA POWER"}, separators=(",", ":")),
            )
        )
    return observations
