from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PERCENTILES = (
    "Worst, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, "
    "60, 65, 70, 75, 80, 85, 90, 95, Top"
)
DEFAULT_LEGEND_ENTRIES = "Worst, 25, 50, 75, Top"


DEFAULT_SETTINGS: dict[str, Any] = {
    "plotMode": "Percentiles",
    "percentiles": DEFAULT_PERCENTILES,
    "legendEntries": DEFAULT_LEGEND_ENTRIES,
    "percentileDisplay": "Lines",
    "percentileLegend": "Colorbar",
    "percentileDash": "Solid",
    "xAxis": "local_hour",
    "yAxis": "relative_value",
    "lineColor": "month",
    "lineShape": "linear",
    "legendPosition": "Inside top right",
    "figureTitle": "Wetbulb Potential Climatology",
    "fontFamily": "Times New Roman",
    "lineWidth": 1.4,
    "markerSize": 0,
    "opacity": 1.0,
    "figureWidth": 500,
    "figureHeight": 400,
    "baseFontSize": 16,
    "titleFontSize": 16,
    "axisTitleFontSize": 16,
    "tickFontSize": 16,
    "legendFontSize": 16,
    "showTitle": True,
    "cycleLineStyles": True,
}


CONTROL_PANELS: list[dict[str, Any]] = [
    {
        "id": "analysis",
        "title": "Analysis",
        "controls": [
            {
                "id": "plotMode",
                "label": "Plot mode",
                "type": "select",
                "options": ["Vehicles", "Percentiles"],
            },
            {"id": "xAxis", "label": "X axis", "type": "select"},
            {"id": "yAxis", "label": "Y axis", "type": "select"},
            {"id": "lineColor", "label": "Line color", "type": "select"},
            {"id": "source", "label": "Data source", "type": "select"},
            {"id": "location", "label": "Location", "type": "select"},
            {"id": "metric", "label": "Metric", "type": "select"},
            {"id": "yearStart", "label": "Year start", "type": "select"},
            {"id": "yearEnd", "label": "Year end", "type": "select"},
        ],
    },
    {
        "id": "percentiles",
        "title": "Percentiles",
        "controls": [
            {"id": "percentiles", "label": "Percentiles", "type": "text"},
            {"id": "legendEntries", "label": "Legend entries", "type": "text"},
            {
                "id": "percentileDisplay",
                "label": "Display",
                "type": "select",
                "options": ["Lines", "Interpolated color field"],
            },
            {
                "id": "percentileLegend",
                "label": "Legend",
                "type": "select",
                "options": ["Legend entries", "Colorbar", "None"],
            },
        ],
    },
    {
        "id": "linesLegend",
        "title": "Lines & Legend",
        "controls": [
            {
                "id": "lineShape",
                "label": "Line shape",
                "type": "select",
                "options": ["linear", "smoothed", "step hv", "step vh"],
            },
            {
                "id": "percentileDash",
                "label": "Percentile dash",
                "type": "select",
                "options": ["Cycle line styles", "Solid", "Dash", "Dot", "Dash-dot"],
            },
            {
                "id": "legendPosition",
                "label": "Legend position",
                "type": "select",
                "options": [
                    "Top",
                    "Bottom",
                    "Right",
                    "Inside top right",
                    "Inside bottom left",
                    "Inside bottom right",
                ],
            },
            {"id": "lineWidth", "label": "Line width", "type": "number"},
            {"id": "markerSize", "label": "Marker size", "type": "number"},
            {"id": "opacity", "label": "Opacity", "type": "number"},
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
            {"id": "saeOptions", "label": "SAE options", "type": "note"},
            {"id": "showTitle", "label": "Show title", "type": "checkbox"},
            {"id": "cycleLineStyles", "label": "Cycle line styles", "type": "checkbox"},
            {"id": "exportSvg", "label": "Export SVG", "type": "button"},
        ],
    },
]


AXES = {
    "x": [
        {"id": "local_hour", "label": "Local hour [h]"},
    ],
    "y": [
        {"id": "relative_value", "label": "Relative wetbulb spread [%]"},
        {"id": "value", "label": "Selected metric value"},
    ],
    "lineColor": [
        {"id": "month", "label": "Month"},
        {"id": "year", "label": "Year"},
        {"id": "source", "label": "Data source"},
        {"id": "location", "label": "Location"},
    ],
}


@dataclass(frozen=True)
class PercentileSpec:
    token: str
    value: float
    label: str


def parse_percentiles(text: str) -> list[PercentileSpec]:
    specs: list[PercentileSpec] = []
    for raw_token in text.split(","):
        token = raw_token.strip()
        if not token:
            continue
        lower = token.lower()
        if lower == "worst":
            specs.append(PercentileSpec("Worst", 0.0, "Worst"))
            continue
        if lower == "top":
            specs.append(PercentileSpec("Top", 100.0, "Top"))
            continue
        clean = token.removesuffix("%").strip()
        try:
            value = float(clean)
        except ValueError as exc:
            raise ValueError(f"Invalid percentile token: {token}") from exc
        if value < 0 or value > 100:
            raise ValueError(f"Percentile out of range 0..100: {token}")
        label = f"{value:g}% Percentile"
        specs.append(PercentileSpec(token, value, label))
    if not specs:
        raise ValueError("At least one percentile is required")
    return specs


def parse_legend_entries(text: str) -> set[str]:
    return {spec.token for spec in parse_percentiles(text)}


def percentile_value(values: list[float], percentile: float) -> float:
    clean_values = sorted(value for value in values if value is not None and not math.isnan(value))
    if not clean_values:
        return float("nan")
    if len(clean_values) == 1:
        return clean_values[0]
    rank = (percentile / 100.0) * (len(clean_values) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return clean_values[low]
    fraction = rank - low
    return clean_values[low] * (1.0 - fraction) + clean_values[high] * fraction


def interpolate_series(
    x_values: list[float],
    y_values: list[float | None],
    x_grid: list[float],
) -> list[float]:
    pairs = sorted(
        (float(x), float(y))
        for x, y in zip(x_values, y_values, strict=False)
        if y is not None and not math.isnan(float(y))
    )
    if not pairs:
        return [float("nan") for _ in x_grid]
    if len(pairs) == 1:
        return [pairs[0][1] for _ in x_grid]
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    out: list[float] = []
    for x in x_grid:
        if x <= xs[0]:
            out.append(ys[0])
            continue
        if x >= xs[-1]:
            out.append(ys[-1])
            continue
        for index in range(1, len(xs)):
            if xs[index] >= x:
                x0, x1 = xs[index - 1], xs[index]
                y0, y1 = ys[index - 1], ys[index]
                fraction = (x - x0) / (x1 - x0)
                out.append(y0 * (1.0 - fraction) + y1 * fraction)
                break
    return out


def compute_percentile_curves(
    series: list[dict[str, Any]],
    percentile_text: str,
    y_key: str = "relative_value",
) -> list[dict[str, Any]]:
    specs = parse_percentiles(percentile_text)
    x_grid = sorted({float(x) for item in series for x in item["x"]})
    interpolated = [
        interpolate_series([float(x) for x in item["x"]], item[y_key], x_grid) for item in series
    ]
    curves: list[dict[str, Any]] = []
    for spec in specs:
        y_values: list[float] = []
        for column_index in range(len(x_grid)):
            column = [row[column_index] for row in interpolated]
            y_values.append(percentile_value(column, spec.value))
        curves.append(
            {
                "token": spec.token,
                "percentile": spec.value,
                "label": spec.label,
                "x": x_grid,
                "y": y_values,
            }
        )
    return curves


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

    location_lookup = {item["id"]: item for item in manifest["locations"]}
    metric_lookup = {item["id"]: item for item in manifest["metrics"]}
    grouped: dict[tuple[str, str, str, int, int], dict[int, sqlite3.Row]] = {}
    max_by_metric: dict[tuple[str, str, str], float] = {}
    for row in rows:
        key = (row["source"], row["location_id"], row["metric"], row["year"], row["month"])
        grouped.setdefault(key, {})[row["hour_local"]] = row
        metric_key = (row["source"], row["location_id"], row["metric"])
        max_by_metric[metric_key] = max(max_by_metric.get(metric_key, 0.0), float(row["mean"]))

    series: list[dict[str, Any]] = []
    for key, hour_rows in grouped.items():
        source, location_id, metric, year, month = key
        metric_info = metric_lookup[metric]
        maximum = max_by_metric[(source, location_id, metric)] or 1.0
        value = [
            float(hour_rows[hour]["mean"]) if hour in hour_rows else None
            for hour in range(24)
        ]
        relative = [
            round((item / maximum) * 100.0, 6) if item is not None else None
            for item in value
        ]
        location = location_lookup[location_id]
        series.append(
            {
                "id": f"{source}:{location_id}:{metric}:{year}:{month:02d}",
                "label": f"{location['name']} {source} {metric_info['label']} {year}-{month:02d}",
                "source": source,
                "location": location_id,
                "locationLabel": location["name"],
                "metric": metric,
                "metricLabel": metric_info["label"],
                "unit": metric_info["unit"],
                "year": year,
                "month": month,
                "monthLabel": f"Month {month:02d}",
                "x": list(range(24)),
                "value": value,
                "relative_value": relative,
                "count": [
                    int(hour_rows[hour]["count"]) if hour in hour_rows else 0
                    for hour in range(24)
                ],
            }
        )

    defaults = dict(DEFAULT_SETTINGS)
    first_availability = manifest["availability"][0] if manifest["availability"] else None
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
        "version": 1,
        "defaults": defaults,
        "panels": CONTROL_PANELS,
        "axes": AXES,
        "sources": manifest["sources"],
        "locations": manifest["locations"],
        "metrics": manifest["metrics"],
        "availability": manifest["availability"],
        "series": series,
        "sourceNote": {
            "title": "Sources and method",
            "html": (
                "Data are derived from <strong>DWD hourly moisture</strong>, "
                "<strong>NOAA Global Hourly / ISD</strong>, and "
                "<strong>NASA POWER hourly</strong>. The plotted quantity is "
                "<strong>dry-bulb temperature minus wet-bulb temperature</strong>; "
                "aggregates are grouped by local station hour and month."
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
