from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .importers.nasa import build_power_url
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
        latitude = float(item["latitude"])
        longitude = float(item["longitude"])
        _validate_coordinate(str(item.get("id") or item.get("site_id")), latitude, longitude)
        data_start = str(item.get("data_start", data.get("defaults", {}).get("year_start", "2002")))
        data_end = str(item.get("data_end", data.get("defaults", {}).get("year_end", "2013")))
        locations.append(
            Location(
                id=str(item["id"]),
                name=str(item["name"]),
                country=str(item.get("country", "")),
                climate_label=str(item.get("climate_label", "")),
                latitude=latitude,
                longitude=longitude,
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
                site_id=str(item.get("site_id", item["id"])),
                site_type=_optional_str(item.get("site_type")),
                region=_optional_str(item.get("region")),
                climate_tags=tuple(str(tag) for tag in item.get("climate_tags", [])),
                priority=int(item["priority"]) if item.get("priority") is not None else None,
                primary_source=_optional_str(item.get("primary_source")),
                secondary_source=_optional_str(item.get("secondary_source")),
                primary_access_url=_primary_access_url(item, latitude, longitude),
                station_candidate_name=_optional_str(item.get("station_candidate_name")),
                station_candidate_id=_optional_str(item.get("station_candidate_id")),
                station_candidate_distance_km=(
                    float(item["station_candidate_distance_km"])
                    if item.get("station_candidate_distance_km") is not None
                    else None
                ),
                wetbulb_method=_optional_str(item.get("wetbulb_method")),
                data_start=data_start,
                data_end=data_end,
                availability_score=(
                    float(item["availability_score"])
                    if item.get("availability_score") is not None
                    else None
                ),
                notes=_optional_str(item.get("notes")),
            )
        )
    return locations


def get_location(location_id: str, path: str | Path = "configs/stations.yml") -> Location:
    for location in load_locations(path):
        if location.id == location_id:
            return location
    raise KeyError(f"Unknown location id: {location_id}")


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _validate_coordinate(location_id: str, latitude: float, longitude: float) -> None:
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"Invalid latitude for {location_id}: {latitude}")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"Invalid longitude for {location_id}: {longitude}")


def _primary_access_url(item: dict[str, Any], latitude: float, longitude: float) -> str | None:
    if item.get("primary_access_url"):
        return str(item["primary_access_url"])
    if item.get("primary_source") == "NASA_POWER_HOURLY_POINT" or item.get("nasa", {}).get(
        "enabled"
    ):
        start = str(item.get("data_start", "2002-01-01")).replace("-", "")
        end = str(item.get("data_end", "2013-12-31")).replace("-", "")
        return build_power_url(latitude, longitude, start, end, "UTC")
    return None
