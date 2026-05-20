from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "source": "",
    "location": "",
    "metric": "delta_t_k",
    "yearStart": 2002,
    "yearEnd": 2013,
    "plotType": "combined",
    "preset": "sae",
    "showValues": False,
    "showTitle": True,
    "showContourLabels": True,
    "figureTitle": "Wetbulb Potential",
    "cmin": 0,
    "cmax": 25,
    "fontFamily": "Times New Roman",
    "figureWidth": 500,
    "figureHeight": 400,
    "baseFontSize": 16,
    "titleFontSize": 16,
    "axisTitleFontSize": 16,
    "tickFontSize": 16,
    "legendFontSize": 16,
}


CONTROL_PANELS: list[dict[str, Any]] = [
    {
        "id": "data",
        "title": "Data",
        "controls": [
            {"id": "source", "label": "Data source", "type": "select"},
            {"id": "location", "label": "Location", "type": "select"},
            {"id": "metric", "label": "Metric", "type": "select"},
            {"id": "yearStart", "label": "Year start", "type": "select"},
            {"id": "yearEnd", "label": "Year end", "type": "select"},
        ],
    },
    {
        "id": "plot",
        "title": "Plot",
        "controls": [
            {"id": "plotType", "label": "Display", "type": "select"},
            {
                "id": "preset",
                "label": "Preset",
                "type": "select",
                "options": [
                    {"id": "sae", "label": "SAE Paper"},
                    {"id": "excel", "label": "Excel Reference"},
                ],
            },
            {"id": "showValues", "label": "Show cell values", "type": "checkbox"},
            {"id": "showContourLabels", "label": "Show isoline labels", "type": "checkbox"},
            {"id": "cmin", "label": "cmin", "type": "number"},
            {"id": "cmax", "label": "cmax", "type": "number"},
        ],
    },
    {
        "id": "figureExport",
        "title": "Figure & Export",
        "controls": [
            {"id": "figureTitle", "label": "Figure title", "type": "text"},
            {"id": "fontFamily", "label": "Font family", "type": "text"},
            {"id": "figureWidth", "label": "Figure width [px]", "type": "number"},
            {"id": "figureHeight", "label": "Figure height [px]", "type": "number"},
            {"id": "baseFontSize", "label": "Base font size", "type": "number"},
            {"id": "titleFontSize", "label": "Title font size", "type": "number"},
            {"id": "axisTitleFontSize", "label": "Axis title font size", "type": "number"},
            {"id": "tickFontSize", "label": "Tick font size", "type": "number"},
            {"id": "legendFontSize", "label": "Legend font size", "type": "number"},
            {"id": "showTitle", "label": "Show title", "type": "checkbox"},
            {"id": "exportSvg", "label": "Export SVG", "type": "button"},
        ],
    },
]


PLOT_TYPES = [
    {"id": "heatmap", "label": "Heatmap"},
    {"id": "contour", "label": "Isolines"},
    {"id": "combined", "label": "Heatmap + isolines"},
]


def build_matrix(
    cells: list[dict[str, Any]],
    source: str,
    location: str,
    metric: str,
    year_start: int,
    year_end: int,
) -> list[list[float | None]]:
    weighted_sum = [[0.0 for _ in range(24)] for _ in range(12)]
    counts = [[0 for _ in range(24)] for _ in range(12)]

    for cell in cells:
        if (
            cell["source"] != source
            or cell["location"] != location
            or cell["metric"] != metric
            or not year_start <= int(cell["year"]) <= year_end
        ):
            continue
        month_index = int(cell["month"]) - 1
        hour = int(cell["hour"])
        count = int(cell["count"])
        if not 0 <= month_index < 12 or not 0 <= hour < 24 or count <= 0:
            continue
        weighted_sum[month_index][hour] += float(cell["mean"]) * count
        counts[month_index][hour] += count

    return [
        [
            round(weighted_sum[month][hour] / counts[month][hour], 6)
            if counts[month][hour]
            else None
            for hour in range(24)
        ]
        for month in range(12)
    ]


def build_visualization_data(data_dir: str | Path) -> dict[str, Any]:
    data_path = Path(data_dir)
    processed_db = data_path / "wetbulb_processed.sqlite"
    manifest_path = data_path / "manifest.json"
    if not processed_db.exists():
        raise FileNotFoundError(f"Missing processed database: {processed_db}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with sqlite3.connect(processed_db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT source, location_id, metric, year, month, hour_local, count, mean
            FROM aggregates
            ORDER BY source, location_id, metric, year, month, hour_local
            """
        ).fetchall()

    cells = [
        {
            "source": row["source"],
            "location": row["location_id"],
            "metric": row["metric"],
            "year": int(row["year"]),
            "month": int(row["month"]),
            "hour": int(row["hour_local"]),
            "count": int(row["count"]),
            "mean": float(row["mean"]),
        }
        for row in rows
    ]

    defaults = dict(DEFAULT_SETTINGS)
    first_availability = _preferred_availability(manifest["availability"])
    if first_availability:
        defaults.update(
            {
                "source": first_availability["source"],
                "location": first_availability["location_id"],
                "metric": "delta_t_k",
                "yearStart": first_availability["year_min"],
                "yearEnd": first_availability["year_max"],
            }
        )

    return {
        "version": 2,
        "defaults": defaults,
        "panels": CONTROL_PANELS,
        "plotTypes": PLOT_TYPES,
        "sources": manifest["sources"],
        "locations": manifest["locations"],
        "metrics": manifest["metrics"],
        "availability": manifest["availability"],
        "cells": cells,
        "sourceNote": {
            "title": "Sources and method",
            "html": (
                "Data are derived from <strong>DWD hourly moisture</strong>, "
                "<strong>NOAA Global Hourly / ISD</strong>, and "
                "<strong>NASA POWER hourly</strong>. The displayed 12 x 24 matrix is "
                "the weighted mean of the selected metric grouped by "
                "<strong>month</strong> and <strong>local station hour</strong>."
            ),
            "links": [
                {
                    "label": "DWD hourly moisture",
                    "url": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/moisture/",
                },
                {
                    "label": "NOAA Global Hourly",
                    "url": "https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database",
                },
                {
                    "label": "NASA POWER Hourly API",
                    "url": "https://power.larc.nasa.gov/docs/services/api/temporal/hourly/",
                },
            ],
        },
    }


def _preferred_availability(availability: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [item for item in availability if item["metric"] == "delta_t_k"] or availability
    if not candidates:
        return None
    source_location_counts = Counter(
        (item["source"], item["location_id"]) for item in candidates
    )
    source_counts = Counter(source for source, _location in source_location_counts)
    return max(
        candidates,
        key=lambda item: (
            source_counts[item["source"]],
            int(item["cells"]),
            int(item["year_max"]) - int(item["year_min"]),
        ),
    )
