from __future__ import annotations

import csv
import json
import zipfile
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from wetbulb_pipeline.models import Location, Observation

SOURCE = "DWD"


def _iter_text_paths(path: Path) -> Iterable[tuple[str, Iterable[str]]]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if Path(name).name.startswith("produkt_") and name.endswith(".txt"):
                    with archive.open(name) as handle:
                        lines = (line.decode("utf-8", errors="replace") for line in handle)
                        yield name, lines
    else:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            yield path.name, handle


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if parsed == -999:
        return None
    return parsed


def read_observations(path: str | Path, location: Location) -> list[Observation]:
    source_path = Path(path)
    observations: list[Observation] = []
    for member_name, lines in _iter_text_paths(source_path):
        reader = csv.DictReader(lines, delimiter=";")
        if reader.fieldnames is None:
            continue
        reader.fieldnames = [field.strip() for field in reader.fieldnames]
        for row in reader:
            cleaned = {key.strip(): value.strip() for key, value in row.items() if key is not None}
            dt = datetime.strptime(cleaned["MESS_DATUM"], "%Y%m%d%H")
            dry = _parse_float(cleaned.get("TT_STD"))
            wet = _parse_float(cleaned.get("TF_STD"))
            dew = _parse_float(cleaned.get("TD_STD"))
            rh = _parse_float(cleaned.get("RF_STD"))
            pressure = _parse_float(cleaned.get("P_STD"))
            valid = dry is not None and wet is not None
            observations.append(
                Observation(
                    source=SOURCE,
                    location_id=location.id,
                    timestamp_utc=f"{dt.isoformat()}Z",
                    timestamp_local=dt.isoformat(),
                    year=dt.year,
                    month=dt.month,
                    hour_local=dt.hour,
                    dry_bulb_c=dry,
                    wet_bulb_c=wet,
                    dew_point_c=dew,
                    relative_humidity_pct=rh,
                    pressure_hpa=pressure,
                    wind_speed_ms=None,
                    solar_radiation_w_m2=None,
                    quality_code=cleaned.get("QN_8"),
                    valid=valid,
                    raw_payload=json.dumps(
                        {"file": member_name, "station": cleaned.get("STATIONS_ID")},
                        separators=(",", ":"),
                    ),
                )
            )
    return observations
