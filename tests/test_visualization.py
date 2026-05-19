from __future__ import annotations

import json
from pathlib import Path

from wetbulb_pipeline.site import build_site
from wetbulb_pipeline.visualization import build_matrix


def test_build_matrix_uses_weighted_mean_over_selected_years() -> None:
    cells = [
        {
            "source": "DWD",
            "location": "stuttgart",
            "metric": "delta_t_k",
            "year": 2002,
            "month": 7,
            "hour": 15,
            "count": 2,
            "mean": 8.0,
        },
        {
            "source": "DWD",
            "location": "stuttgart",
            "metric": "delta_t_k",
            "year": 2003,
            "month": 7,
            "hour": 15,
            "count": 1,
            "mean": 11.0,
        },
        {
            "source": "DWD",
            "location": "stuttgart",
            "metric": "delta_t_k",
            "year": 2004,
            "month": 7,
            "hour": 15,
            "count": 1,
            "mean": 100.0,
        },
    ]

    matrix = build_matrix(cells, "DWD", "stuttgart", "delta_t_k", 2002, 2003)

    assert matrix[6][15] == 9.0
    assert matrix[0][0] is None


def test_static_site_schema_controls_and_defaults(tmp_path: Path) -> None:
    out = tmp_path / "site"
    build_site("web/public/data", out)

    assert (out / "index.html").exists()
    assert (out / ".nojekyll").exists()
    data_path = out / "assets" / "data.json"
    assert data_path.exists()

    data = json.loads(data_path.read_text(encoding="utf-8"))
    index = (out / "index.html").read_text(encoding="utf-8")

    assert data["defaults"]["plotType"] == "combined"
    assert data["defaults"]["fontFamily"] == "Times New Roman"
    assert data["defaults"]["figureWidth"] == 500
    assert data["defaults"]["figureHeight"] == 400
    assert data["defaults"]["baseFontSize"] == 16
    assert data["defaults"]["titleFontSize"] == 16
    assert data["defaults"]["axisTitleFontSize"] == 16
    assert data["defaults"]["tickFontSize"] == 16
    assert data["defaults"]["legendFontSize"] == 16
    assert data["defaults"]["showTitle"] is True
    assert data["defaults"]["showContourLabels"] is True
    assert data["plotTypes"] == [
        {"id": "heatmap", "label": "Heatmap"},
        {"id": "contour", "label": "Isolines"},
        {"id": "combined", "label": "Heatmap + isolines"},
    ]

    for panel in ["Data", "Plot", "Figure & Export"]:
        assert panel in index
    assert "Locations" in index
    assert 'id="locationMap"' in index
    assert "updateLocationMap" in index
    assert "selectLocationFromMap" in index
    assert "plotly_click" in index
    assert "scattergeo" in index
    assert all("latitude" in location and "longitude" in location for location in data["locations"])
    for control in [
        "Data source",
        "Location",
        "Metric",
        "Year start",
        "Year end",
        "Display",
        "Preset",
        "Show cell values",
        "Show isoline labels",
        "Figure title",
        "Font family",
        "Figure width [px]",
        "Figure height [px]",
        "Base font size",
        "Title font size",
        "Axis title font size",
        "Tick font size",
        "Legend font size",
        "Show title",
        "Export SVG",
    ]:
        assert control in index
