from __future__ import annotations

import argparse
from pathlib import Path

from .config import get_location, load_locations
from .database import (
    connect,
    create_import_batch,
    init_raw_db,
    upsert_locations,
    upsert_observations,
)
from .export import DEFAULT_EXPORT_METRICS, METRICS, export_processed
from .importers import dwd, nasa, noaa
from .site import build_site
from .sync import update_all

DEFAULT_CONFIG = "configs/stations.yml"
DEFAULT_RAW_DB = "data/raw/wetbulb_raw.sqlite"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="wetbulb_pipeline")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db")
    init_parser.add_argument("--db", default=DEFAULT_RAW_DB)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--db", default=DEFAULT_RAW_DB)
    import_sources = import_parser.add_subparsers(dest="source", required=True)

    dwd_parser = import_sources.add_parser("dwd")
    dwd_parser.add_argument("--file", required=True)
    dwd_parser.add_argument("--location", default="stuttgart-neckartal")

    noaa_parser = import_sources.add_parser("noaa")
    noaa_parser.add_argument("--location", required=True)
    noaa_parser.add_argument(
        "--years",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        default=(2002, 2013),
    )
    noaa_parser.add_argument("--download-dir", default="data/raw/downloads/noaa")

    nasa_parser = import_sources.add_parser("nasa")
    nasa_parser.add_argument("--location", required=True)
    nasa_parser.add_argument("--start", default="20020101")
    nasa_parser.add_argument("--end", default="20131231")
    nasa_parser.add_argument("--download-dir", default="data/raw/downloads/nasa")
    nasa_parser.add_argument("--time-standard", choices=["UTC", "LST"], default="UTC")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--raw-db", default=DEFAULT_RAW_DB)
    export_parser.add_argument("--processed-db", default="web/public/data/wetbulb_processed.sqlite")
    export_parser.add_argument("--manifest", default="web/public/data/manifest.json")
    export_parser.add_argument("--max-mb", type=float, default=100)
    export_parser.add_argument(
        "--metrics",
        nargs="+",
        choices=[*METRICS.keys(), "all"],
        default=list(DEFAULT_EXPORT_METRICS),
        help="Metrics to export for Pages. Use 'all' for a larger local analysis database.",
    )

    build_demo_parser = subparsers.add_parser("build-demo")
    build_demo_parser.add_argument("--db", default=DEFAULT_RAW_DB)
    build_demo_parser.add_argument(
        "--dwd-file",
        default="produkt_tf_stunde_20021101_20130514_04926.txt",
    )

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--db", default=DEFAULT_RAW_DB)
    update_parser.add_argument("--years", nargs=2, type=int, default=(2002, 2013))
    update_parser.add_argument(
        "--sources",
        nargs="+",
        choices=["dwd", "noaa", "nasa"],
        default=["dwd", "noaa", "nasa"],
    )
    update_parser.add_argument("--processed-db", default="web/public/data/wetbulb_processed.sqlite")
    update_parser.add_argument("--manifest", default="web/public/data/manifest.json")
    update_parser.add_argument(
        "--metrics",
        nargs="+",
        choices=[*METRICS.keys(), "all"],
        default=list(DEFAULT_EXPORT_METRICS),
        help="Metrics to export after update. Use 'all' for a larger local analysis database.",
    )
    update_parser.add_argument("--dry-run", action="store_true")
    update_parser.add_argument("--no-export", action="store_true")
    update_parser.add_argument("--quiet", action="store_true")

    site_parser = subparsers.add_parser("site")
    site_parser.add_argument("--data", default="web/public/data")
    site_parser.add_argument("--out", default="site")

    dash_parser = subparsers.add_parser("dash")
    dash_parser.add_argument("--data", default="web/public/data")
    dash_parser.add_argument("--host", default="127.0.0.1")
    dash_parser.add_argument("--port", type=int, default=8050)
    dash_parser.add_argument("--debug", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "init-db":
        _init_db(args.db, args.config)
    elif args.command == "import":
        _import(args)
    elif args.command == "export":
        export_processed(
            args.raw_db,
            args.processed_db,
            args.manifest,
            max_bytes=int(args.max_mb * 1024 * 1024),
            metrics=_normalize_metrics(args.metrics),
        )
    elif args.command == "build-demo":
        _init_db(args.db, args.config)
        location = get_location("stuttgart-neckartal", args.config)
        _import_observations(
            args.db,
            location,
            dwd.read_observations(args.dwd_file, location),
            args.dwd_file,
        )
        export_processed(args.db)
    elif args.command == "update":
        results = update_all(
            args.config,
            args.db,
            tuple(args.years),
            [source for source in args.sources],
            export_after=not args.no_export,
            processed_db=args.processed_db,
            manifest_path=args.manifest,
            export_metrics=_normalize_metrics(args.metrics),
            dry_run=args.dry_run,
            progress=None if args.quiet else _print_progress,
        )
        for result in results:
            status = "skip" if result.skipped else "sync"
            print(
                f"{status}\t{result.source}\t{result.location_id}\t"
                f"{result.imported}\t{result.input_ref}",
                flush=True,
            )
    elif args.command == "site":
        build_site(args.data, args.out)
        print(f"Built static site in {args.out}")
    elif args.command == "dash":
        from .dash_app import run_dash

        run_dash(args.data, args.host, args.port, args.debug)


def _init_db(db_path: str, config_path: str) -> None:
    init_raw_db(db_path)
    with connect(db_path) as conn:
        upsert_locations(conn, load_locations(config_path))
        conn.commit()


def _import(args: argparse.Namespace) -> None:
    _init_db(args.db, args.config)
    location = get_location(args.location, args.config)
    if args.source == "dwd":
        observations = dwd.read_observations(args.file, location)
        _import_observations(args.db, location, observations, args.file, "DWD")
    elif args.source == "noaa":
        if not location.noaa_station_id:
            raise ValueError(f"Location {location.id} has no NOAA station id")
        start, end = args.years
        files: list[Path] = [
            noaa.download_year(location.noaa_station_id, year, args.download_dir)
            for year in range(start, end + 1)
        ]
        observations = []
        for file_path in files:
            observations.extend(noaa.read_observations(file_path, location))
        _import_observations(
            args.db,
            location,
            observations,
            ",".join(str(path) for path in files),
            "NOAA",
        )
    elif args.source == "nasa":
        if not location.nasa_enabled:
            raise ValueError(f"Location {location.id} is not enabled for NASA POWER")
        file_path = nasa.download_range(
            location, args.start, args.end, args.download_dir, args.time_standard
        )
        observations = nasa.read_observations(file_path, location, args.time_standard)
        _import_observations(args.db, location, observations, str(file_path), "NASA_POWER")


def _import_observations(
    db_path: str,
    location,
    observations,
    input_ref: str,
    source: str | None = None,
) -> None:
    with connect(db_path) as conn:
        batch_id = create_import_batch(
            conn,
            source or (observations[0].source if observations else "unknown"),
            location.id,
            input_ref,
        )
        count = upsert_observations(conn, observations, batch_id)
        conn.commit()
    print(f"Imported {count} observations for {location.id}")


def _print_progress(message: str) -> None:
    print(message, flush=True)


def _normalize_metrics(metrics: list[str]) -> list[str]:
    if "all" in metrics:
        return list(METRICS)
    return metrics
