from __future__ import annotations

import json
from pathlib import Path

from wetbulb_pipeline.site import build_site
from wetbulb_pipeline.visualization import (
    DEFAULT_PERCENTILES,
    compute_percentile_curves,
    parse_percentiles,
)


def test_percentile_parser_supports_required_defaults() -> None:
    specs = parse_percentiles(DEFAULT_PERCENTILES)

    assert specs[0].token == "Worst"
    assert specs[0].value == 0
    assert specs[-1].token == "Top"
    assert specs[-1].value == 100
    assert any(spec.label == "25% Percentile" for spec in specs)


def test_percentile_computation_interpolates_to_common_x_grid() -> None:
    series = [
        {"x": [0, 2], "relative_value": [0.0, 20.0]},
        {"x": [0, 1, 2], "relative_value": [10.0, 20.0, 30.0]},
    ]

    curves = compute_percentile_curves(series, "Worst, 50, Top")

    assert curves[0]["label"] == "Worst"
    assert curves[0]["x"] == [0.0, 1.0, 2.0]
    assert curves[0]["y"] == [0.0, 10.0, 20.0]
    assert curves[1]["label"] == "50% Percentile"
    assert curves[1]["y"] == [5.0, 15.0, 25.0]
    assert curves[2]["label"] == "Top"
    assert curves[2]["y"] == [10.0, 20.0, 30.0]


def test_static_site_schema_controls_and_defaults(tmp_path: Path) -> None:
    out = tmp_path / "site"
    build_site("web/public/data", out)

    assert (out / "index.html").exists()
    assert (out / ".nojekyll").exists()
    data_path = out / "assets" / "data.json"
    assert data_path.exists()

    data = json.loads(data_path.read_text(encoding="utf-8"))
    index = (out / "index.html").read_text(encoding="utf-8")

    assert data["defaults"]["plotMode"] == "Percentiles"
    assert data["defaults"]["fontFamily"] == "Times New Roman"
    assert data["defaults"]["lineWidth"] == 1.4
    assert data["defaults"]["markerSize"] == 0
    assert data["defaults"]["legendPosition"] == "Inside top right"
    assert data["defaults"]["percentileDisplay"] == "Lines"
    assert data["defaults"]["percentileLegend"] == "Colorbar"
    assert data["defaults"]["percentileDash"] == "Solid"
    assert data["defaults"]["figureWidth"] == 500
    assert data["defaults"]["figureHeight"] == 400
    assert data["defaults"]["baseFontSize"] == 16
    assert data["defaults"]["titleFontSize"] == 16
    assert data["defaults"]["axisTitleFontSize"] == 16
    assert data["defaults"]["tickFontSize"] == 16
    assert data["defaults"]["legendFontSize"] == 16
    assert data["defaults"]["showTitle"] is True
    assert data["defaults"]["cycleLineStyles"] is True

    for panel in ["Analysis", "Percentiles", "Lines & Legend", "Figure & Export"]:
        assert panel in index
    for control in [
        "Plot mode",
        "X axis",
        "Y axis",
        "Line color",
        "Percentiles",
        "Legend entries",
        "Display",
        "Legend",
        "Line shape",
        "Percentile dash",
        "Legend position",
        "Line width",
        "Marker size",
        "Opacity",
        "Figure title",
        "Font family",
        "Figure width [px]",
        "Figure height [px]",
        "Base font size",
        "Title font size",
        "Axis title font size",
        "Tick font size",
        "Legend font size",
        "SAE options",
        "Show title",
        "Cycle line styles",
        "Export SVG",
    ]:
        assert control in index
