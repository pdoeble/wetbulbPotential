from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Literal

from .config import load_locations, load_station_config
from .database import (
    connect,
    create_import_batch,
    init_raw_db,
    upsert_locations,
    upsert_observations,
)
from .export import DEFAULT_EXPORT_METRICS, export_processed
from .importers import dwd, nasa, noaa
from .models import Location

SourceName = Literal["dwd", "noaa", "nasa"]
ProgressCallback = Callable[[str], None]

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


@dataclass
class _Progress:
    callback: ProgressCallback | None
    total_steps: int
    current_step: int = 0
    started_at: float = field(default_factory=perf_counter)

    def emit(self, message: str) -> None:
        if self.callback is None:
            return
        self.callback(f"{_format_elapsed(perf_counter() - self.started_at)} {message}")

    def begin_step(self, source: str, location_id: str, detail: str) -> None:
        self.current_step += 1
        self.emit(f"{self.step_label} {source} {location_id}: {detail}")

    def status(self, source: str, location_id: str, detail: str) -> None:
        self.emit(f"{self.step_label} {source} {location_id}: {detail}")

    @property
    def step_label(self) -> str:
        if self.total_steps <= 0:
            return "[0000/0000]"
        return f"[{self.current_step:04d}/{self.total_steps:04d}]"

    def download_hook(self, label: str) -> Callable[[int, int, int], None]:
        last_percent_bucket = -1
        last_unknown_bytes = 0

        def report(block_count: int, block_size: int, total_size: int) -> None:
            nonlocal last_percent_bucket, last_unknown_bytes
            bytes_seen = max(0, block_count * block_size)
            if total_size and total_size > 0:
                percent = min(100, int(bytes_seen * 100 / total_size))
                percent_bucket = percent // 10
                if percent_bucket != last_percent_bucket or percent == 100:
                    last_percent_bucket = percent_bucket
                    self.emit(
                        f"{self.step_label} {label}: download {percent:3d}% "
                        f"({_format_bytes(bytes_seen)}/{_format_bytes(total_size)})"
                    )
                return
            if bytes_seen - last_unknown_bytes >= 5 * 1024 * 1024:
                last_unknown_bytes = bytes_seen
                self.emit(
                    f"{self.step_label} {label}: downloaded {_format_bytes(bytes_seen)}"
                )

        return report


def update_all(
    config_path: str | Path,
    raw_db: str | Path,
    years: tuple[int, int],
    sources: list[SourceName],
    export_after: bool = True,
    processed_db: str | Path = "web/public/data/wetbulb_processed.sqlite",
    manifest_path: str | Path = "web/public/data/manifest.json",
    export_metrics: list[str] | tuple[str, ...] | None = DEFAULT_EXPORT_METRICS,
    dry_run: bool = False,
    progress: ProgressCallback | None = None,
) -> list[SyncResult]:
    init_raw_db(raw_db)
    locations = load_locations(config_path)
    progress_state = _Progress(progress, _count_work_items(locations, years, sources))
    progress_state.emit(
        "Starting update: "
        f"{len(locations)} locations, years {years[0]}-{years[1]}, "
        f"sources {', '.join(sources)}, dry_run={dry_run}"
    )
    with connect(raw_db) as conn:
        progress_state.emit(f"Preparing raw database: {raw_db}")
        upsert_locations(conn, locations)
        conn.commit()

    config = load_station_config(config_path)
    results: list[SyncResult] = []
    for location_index, location in enumerate(locations, start=1):
        progress_state.emit(
            f"Location {location_index}/{len(locations)}: {location.name} ({location.id})"
        )
        item = _location_config(config, location.id)
        if "dwd" in sources and location.dwd_station_id:
            results.append(
                _sync_dwd(raw_db, location, item.get("dwd", {}), dry_run, progress_state)
            )
        if "noaa" in sources and location.noaa_station_id:
            results.extend(_sync_noaa(raw_db, location, years, dry_run, progress_state))
        if "nasa" in sources and location.nasa_enabled:
            results.extend(_sync_nasa(raw_db, location, years, dry_run, progress_state))

    if export_after and not dry_run:
        progress_state.emit(f"Exporting processed data: {processed_db}")
        export_years = _export_years(config, years)
        export_processed(
            raw_db,
            processed_db,
            manifest_path,
            metrics=export_metrics,
            years=export_years,
        )
        progress_state.emit(f"Export complete: {processed_db}; manifest {manifest_path}")
    progress_state.emit(f"Finished update: {len(results)} result rows")
    return results


def _location_config(config: dict, location_id: str) -> dict:
    for item in config["locations"]:
        if item["id"] == location_id:
            return item
    raise KeyError(location_id)


def _export_years(config: dict, update_years: tuple[int, int]) -> tuple[int, int]:
    default_start = int(config.get("defaults", {}).get("year_start", update_years[0]))
    return default_start, int(update_years[1])


def _sync_dwd(
    raw_db: str | Path,
    location: Location,
    dwd_config: dict,
    dry_run: bool,
    progress: _Progress,
) -> SyncResult:
    progress.begin_step("DWD", location.id, f"station {location.dwd_station_id}")
    if _has_any_observations(raw_db, "DWD", location.id):
        progress.status("DWD", location.id, "skip; raw DB already contains observations")
        return SyncResult("DWD", location.id, "raw-db", 0, True)

    local_file = dwd_config.get("local_file")
    historical_file = dwd_config.get("historical_file")
    if local_file and Path(local_file).exists():
        input_path = Path(local_file)
        progress.status("DWD", location.id, f"use local file {input_path}")
    elif historical_file:
        input_path = Path("data/raw/downloads/dwd") / historical_file
        if not input_path.exists() and not dry_run:
            url = f"{DWD_BASE_URL}/{historical_file}"
            progress.status("DWD", location.id, f"download {url}")
            _download_file(
                url,
                input_path,
                reporthook=progress.download_hook(f"DWD {location.id}"),
            )
        else:
            progress.status("DWD", location.id, f"use cached file {input_path}")
    else:
        progress.status("DWD", location.id, "skip; missing DWD configuration")
        return SyncResult("DWD", location.id, "missing-config", 0, True)

    if dry_run:
        progress.status("DWD", location.id, f"dry-run would import {input_path}")
        return SyncResult("DWD", location.id, str(input_path), 0, False)

    progress.status("DWD", location.id, f"read {input_path}")
    observations = dwd.read_observations(input_path, location)
    progress.status("DWD", location.id, f"store {len(observations):,} observations")
    imported = _store_observations(raw_db, "DWD", location.id, str(input_path), observations)
    progress.status("DWD", location.id, f"done; imported {imported:,} observations")
    return SyncResult("DWD", location.id, str(input_path), imported, False)


def _sync_noaa(
    raw_db: str | Path,
    location: Location,
    years: tuple[int, int],
    dry_run: bool,
    progress: _Progress,
) -> list[SyncResult]:
    assert location.noaa_station_id is not None
    results: list[SyncResult] = []
    download_dir = Path("data/raw/downloads/noaa") / location.noaa_station_id
    for year in range(years[0], years[1] + 1):
        progress.begin_step("NOAA", location.id, f"{year}, station {location.noaa_station_id}")
        if _has_year(raw_db, "NOAA", location.id, year):
            progress.status("NOAA", location.id, f"{year} skip; year already imported")
            results.append(SyncResult("NOAA", location.id, str(year), 0, True))
            continue
        input_path = download_dir / f"{location.noaa_station_id}_{year}.csv"
        missing_marker = noaa.missing_marker_path(location.noaa_station_id, year, download_dir)
        if missing_marker.exists():
            progress.status("NOAA", location.id, f"{year} skip; missing marker {missing_marker}")
            results.append(SyncResult("NOAA", location.id, f"missing:{missing_marker}", 0, True))
            continue
        if dry_run:
            progress.status("NOAA", location.id, f"{year} dry-run would import {input_path}")
            results.append(SyncResult("NOAA", location.id, str(input_path), 0, False))
            continue
        if not input_path.exists():
            url = noaa.build_year_url(location.noaa_station_id, year)
            progress.status("NOAA", location.id, f"{year} download {url}")
            input_path = noaa.download_year(
                location.noaa_station_id,
                year,
                download_dir,
                reporthook=progress.download_hook(f"NOAA {location.id} {year}"),
            )
            if input_path is None:
                progress.status("NOAA", location.id, f"{year} skip; remote file missing")
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
        else:
            progress.status("NOAA", location.id, f"{year} use cached file {input_path}")
        progress.status("NOAA", location.id, f"{year} read {input_path}")
        observations = noaa.read_observations(input_path, location)
        progress.status("NOAA", location.id, f"{year} store {len(observations):,} observations")
        imported = _store_observations(raw_db, "NOAA", location.id, str(input_path), observations)
        progress.status("NOAA", location.id, f"{year} done; imported {imported:,} observations")
        results.append(SyncResult("NOAA", location.id, str(input_path), imported, False))
    return results


def _sync_nasa(
    raw_db: str | Path,
    location: Location,
    years: tuple[int, int],
    dry_run: bool,
    progress: _Progress,
) -> list[SyncResult]:
    results: list[SyncResult] = []
    download_dir = Path("data/raw/downloads/nasa") / location.id
    for year in range(years[0], years[1] + 1):
        progress.begin_step("NASA_POWER", location.id, f"{year}")
        if _has_year(raw_db, "NASA_POWER", location.id, year):
            progress.status("NASA_POWER", location.id, f"{year} skip; year already imported")
            results.append(SyncResult("NASA_POWER", location.id, str(year), 0, True))
            continue
        input_path = download_dir / f"{location.id}_{year}0101_{year}1231_UTC.csv"
        if dry_run:
            progress.status("NASA_POWER", location.id, f"{year} dry-run would import {input_path}")
            results.append(SyncResult("NASA_POWER", location.id, str(input_path), 0, False))
            continue
        if not input_path.exists():
            url = nasa.build_power_url(
                location.latitude,
                location.longitude,
                f"{year}0101",
                f"{year}1231",
                "UTC",
            )
            progress.status("NASA_POWER", location.id, f"{year} download {url}")
            input_path = nasa.download_range(
                location,
                f"{year}0101",
                f"{year}1231",
                download_dir,
                time_standard="UTC",
                reporthook=progress.download_hook(f"NASA_POWER {location.id} {year}"),
            )
        else:
            progress.status("NASA_POWER", location.id, f"{year} use cached file {input_path}")
        progress.status("NASA_POWER", location.id, f"{year} read {input_path}")
        observations = nasa.read_observations(input_path, location, time_standard="UTC")
        progress.status(
            "NASA_POWER", location.id, f"{year} store {len(observations):,} observations"
        )
        imported = _store_observations(
            raw_db, "NASA_POWER", location.id, str(input_path), observations
        )
        progress.status(
            "NASA_POWER", location.id, f"{year} done; imported {imported:,} observations"
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


def _download_file(
    url: str,
    target: Path,
    reporthook: Callable[[int, int, int], None] | None = None,
) -> None:
    from urllib.request import urlretrieve

    target.parent.mkdir(parents=True, exist_ok=True)
    if reporthook is None:
        urlretrieve(url, target)
    else:
        urlretrieve(url, target, reporthook=reporthook)


def _count_work_items(
    locations: list[Location], years: tuple[int, int], sources: list[SourceName]
) -> int:
    year_count = max(0, years[1] - years[0] + 1)
    total = 0
    for location in locations:
        if "dwd" in sources and location.dwd_station_id:
            total += 1
        if "noaa" in sources and location.noaa_station_id:
            total += year_count
        if "nasa" in sources and location.nasa_enabled:
            total += year_count
    return total


def _format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if amount < 1024.0 or unit == "GB":
            return f"{amount:.1f} {unit}"
        amount /= 1024.0
    return f"{amount:.1f} GB"


def _format_elapsed(seconds: float) -> str:
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
