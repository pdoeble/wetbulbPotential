from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .config import load_locations, load_station_config
from .database import (
    connect,
    create_import_batch,
    init_raw_db,
    upsert_locations,
    upsert_observations,
)
from .export import export_processed
from .importers import dwd, nasa, noaa
from .models import Location

SourceName = Literal["dwd", "noaa", "nasa"]

DWD_BASE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/hourly/moisture/historical"
)


@dataclass(frozen=True)
class SyncResult:
    source: str
    location_id: str
    input_ref: str
    imported: int
    skipped: bool


def update_all(
    config_path: str | Path,
    raw_db: str | Path,
    years: tuple[int, int],
    sources: list[SourceName],
    export_after: bool = True,
    processed_db: str | Path = "web/public/data/wetbulb_processed.sqlite",
    manifest_path: str | Path = "web/public/data/manifest.json",
    dry_run: bool = False,
) -> list[SyncResult]:
    init_raw_db(raw_db)
    locations = load_locations(config_path)
    with connect(raw_db) as conn:
        upsert_locations(conn, locations)
        conn.commit()

    config = load_station_config(config_path)
    results: list[SyncResult] = []
    for location in locations:
        item = _location_config(config, location.id)
        if "dwd" in sources and location.dwd_station_id:
            results.append(_sync_dwd(raw_db, location, item.get("dwd", {}), dry_run))
        if "noaa" in sources and location.noaa_station_id:
            results.extend(_sync_noaa(raw_db, location, years, dry_run))
        if "nasa" in sources and location.nasa_enabled:
            results.extend(_sync_nasa(raw_db, location, years, dry_run))

    if export_after and not dry_run:
        export_processed(raw_db, processed_db, manifest_path)
    return results


def _location_config(config: dict, location_id: str) -> dict:
    for item in config["locations"]:
        if item["id"] == location_id:
            return item
    raise KeyError(location_id)


def _sync_dwd(
    raw_db: str | Path, location: Location, dwd_config: dict, dry_run: bool
) -> SyncResult:
    if _has_any_observations(raw_db, "DWD", location.id):
        return SyncResult("DWD", location.id, "raw-db", 0, True)

    local_file = dwd_config.get("local_file")
    historical_file = dwd_config.get("historical_file")
    if local_file and Path(local_file).exists():
        input_path = Path(local_file)
    elif historical_file:
        input_path = Path("data/raw/downloads/dwd") / historical_file
        if not input_path.exists() and not dry_run:
            _download_file(f"{DWD_BASE_URL}/{historical_file}", input_path)
    else:
        return SyncResult("DWD", location.id, "missing-config", 0, True)

    if dry_run:
        return SyncResult("DWD", location.id, str(input_path), 0, False)

    observations = dwd.read_observations(input_path, location)
    imported = _store_observations(raw_db, "DWD", location.id, str(input_path), observations)
    return SyncResult("DWD", location.id, str(input_path), imported, False)


def _sync_noaa(
    raw_db: str | Path, location: Location, years: tuple[int, int], dry_run: bool
) -> list[SyncResult]:
    assert location.noaa_station_id is not None
    results: list[SyncResult] = []
    download_dir = Path("data/raw/downloads/noaa") / location.noaa_station_id
    for year in range(years[0], years[1] + 1):
        if _has_year(raw_db, "NOAA", location.id, year):
            results.append(SyncResult("NOAA", location.id, str(year), 0, True))
            continue
        input_path = download_dir / f"{location.noaa_station_id}_{year}.csv"
        missing_marker = noaa.missing_marker_path(location.noaa_station_id, year, download_dir)
        if missing_marker.exists():
            results.append(SyncResult("NOAA", location.id, f"missing:{missing_marker}", 0, True))
            continue
        if dry_run:
            results.append(SyncResult("NOAA", location.id, str(input_path), 0, False))
            continue
        if not input_path.exists():
            input_path = noaa.download_year(location.noaa_station_id, year, download_dir)
            if input_path is None:
                results.append(
                    SyncResult(
                        "NOAA",
                        location.id,
                        f"missing:{noaa.build_year_url(location.noaa_station_id, year)}",
                        0,
                        True,
                    )
                )
                continue
        observations = noaa.read_observations(input_path, location)
        imported = _store_observations(raw_db, "NOAA", location.id, str(input_path), observations)
        results.append(SyncResult("NOAA", location.id, str(input_path), imported, False))
    return results


def _sync_nasa(
    raw_db: str | Path, location: Location, years: tuple[int, int], dry_run: bool
) -> list[SyncResult]:
    results: list[SyncResult] = []
    download_dir = Path("data/raw/downloads/nasa") / location.id
    for year in range(years[0], years[1] + 1):
        if _has_year(raw_db, "NASA_POWER", location.id, year):
            results.append(SyncResult("NASA_POWER", location.id, str(year), 0, True))
            continue
        input_path = download_dir / f"{location.id}_{year}0101_{year}1231_UTC.csv"
        if dry_run:
            results.append(SyncResult("NASA_POWER", location.id, str(input_path), 0, False))
            continue
        if not input_path.exists():
            input_path = nasa.download_range(
                location,
                f"{year}0101",
                f"{year}1231",
                download_dir,
                time_standard="UTC",
            )
        observations = nasa.read_observations(input_path, location, time_standard="UTC")
        imported = _store_observations(
            raw_db, "NASA_POWER", location.id, str(input_path), observations
        )
        results.append(SyncResult("NASA_POWER", location.id, str(input_path), imported, False))
    return results


def _store_observations(
    raw_db: str | Path, source: str, location_id: str, input_ref: str, observations
) -> int:
    with connect(raw_db) as conn:
        batch_id = create_import_batch(conn, source, location_id, input_ref)
        imported = upsert_observations(conn, observations, batch_id)
        conn.commit()
    return imported


def _has_any_observations(raw_db: str | Path, source: str, location_id: str) -> bool:
    if not Path(raw_db).exists():
        return False
    with connect(raw_db) as conn:
        row = conn.execute(
            """
            SELECT 1 FROM observations
            WHERE source = ? AND location_id = ?
            LIMIT 1
            """,
            (source, location_id),
        ).fetchone()
    return row is not None


def _has_year(raw_db: str | Path, source: str, location_id: str, year: int) -> bool:
    if not Path(raw_db).exists():
        return False
    with connect(raw_db) as conn:
        row = conn.execute(
            """
            SELECT 1 FROM observations
            WHERE source = ? AND location_id = ? AND year = ?
            LIMIT 1
            """,
            (source, location_id, year),
        ).fetchone()
    return row is not None


def _download_file(url: str, target: Path) -> None:
    from urllib.request import urlretrieve

    target.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, target)
