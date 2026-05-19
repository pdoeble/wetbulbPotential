from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Location


def load_station_config(path: str | Path = "configs/stations.yml") -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or "locations" not in data:
        raise ValueError(f"Station config {path} must contain a locations list")
    return data


def load_locations(path: str | Path = "configs/stations.yml") -> list[Location]:
    data = load_station_config(path)
    locations: list[Location] = []
    for item in data["locations"]:
        locations.append(
            Location(
                id=str(item["id"]),
                name=str(item["name"]),
                country=str(item.get("country", "")),
                climate_label=str(item.get("climate_label", "")),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                elevation_m=(
                    float(item["elevation_m"]) if item.get("elevation_m") is not None else None
                ),
                timezone=str(item.get("timezone", "UTC")),
                dwd_station_id=(
                    str(item.get("dwd", {}).get("station_id"))
                    if item.get("dwd", {}).get("station_id") is not None
                    else None
                ),
                noaa_station_id=(
                    str(item.get("noaa", {}).get("station_id"))
                    if item.get("noaa", {}).get("station_id") is not None
                    else None
                ),
                nasa_enabled=bool(item.get("nasa", {}).get("enabled", False)),
            )
        )
    return locations


def get_location(location_id: str, path: str | Path = "configs/stations.yml") -> Location:
    for location in load_locations(path):
        if location.id == location_id:
            return location
    raise KeyError(f"Unknown location id: {location_id}")

