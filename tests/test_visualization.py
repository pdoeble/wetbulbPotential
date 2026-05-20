from __future__ import annotations

import json
from pathlib import Path

from wetbulb_pipeline.dash_app import (
    availability_for_selection,
    build_dash_figure,
    build_location_map_figure,
    preferred_availability_for_location,
)
from wetbulb_pipeline.site import build_site
from wetbulb_pipeline.visualization import build_matrix, build_visualization_data


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
    assert data["defaults"]["source"] == "NASA_POWER"
    assert data["defaults"]["figureTitle"] == "Wetbulb Potential"
    assert "Climatology" not in data["defaults"]["figureTitle"]
    assert data["defaults"]["cmin"] == 0
    assert data["defaults"]["cmax"] == 16
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
    assert data["defaults"]["colorFillMode"] == "interpolated"
    assert data["defaults"]["isolineStart"] == 0
    assert data["defaults"]["isolineStep"] == 1
    assert data["defaults"]["mapPreset"] == "world"
    assert data["defaults"]["mapViewport"] == "[-180,180,-90,90]"
    default_availability = availability_for_selection(
        data,
        data["defaults"]["source"],
        data["defaults"]["location"],
        data["defaults"]["metric"],
    )
    assert default_availability is not None
    assert data["defaults"]["yearStart"] == default_availability["year_min"]
    assert data["defaults"]["yearEnd"] == default_availability["year_max"]
    assert data["plotTypes"] == [
        {"id": "heatmap", "label": "Heatmap"},
        {"id": "contour", "label": "Isolines"},
        {"id": "combined", "label": "Heatmap + isolines"},
    ]
    assert "combinedContour" in index
    assert "colorTrace" in index
    assert "contourSettings" in index
    assert "coloring: 'none'" in index
    assert "coloring: 'heatmap'" in index
    assert "state.colorFillMode === 'grid'" in index
    assert "isolineStart" in index
    assert "isolineStep" in index

    for panel in ["Data", "Plot", "Map", "Figure & Export"]:
        assert panel in index
    assert "Locations" in index
    assert 'id="locationMap"' in index
    assert "updateLocationMap" in index
    assert "selectLocationFromMap" in index
    assert "plotly_click" in index
    assert "scattergeo" in index
    assert "exportPlotSvg" in index
    assert "exportMapSvg" in index
    assert "Export map SVG" in index
    assert "wetbulb-location-map" in index
    assert "scrollZoom: true" in index
    assert "Map viewport [lon_min,lon_max,lat_min,lat_max]" in index
    assert "Map preset" in index
    assert "Europe" in index
    assert "North America" in index
    assert "Middle East" in index
    assert "Asia (India to Japan)" in index
    assert "MAP_VIEWPORT_PRESETS" in index
    assert "asia_india_japan" in index
    assert "formatMapViewportFromLayout" in index
    assert "geoFromViewportText" in index
    assert "uirevision: 'location-map'" in index
    assert "<strong>${location.name}</strong>" not in index
    assert "refreshDependentOptions(true)" in index
    assert "availableYears(resetYearRange = false)" in index
    assert "MONTH_LABELS" in index
    assert "HOUR_TICKS" in index
    assert "plotTitle" in index
    assert "colorLimits" in index
    assert all("latitude" in location and "longitude" in location for location in data["locations"])
    for control in [
        "Data source",
        "Location",
        "Metric",
        "Year start",
        "Year end",
        "Display",
        "Color fill",
        "Interpolated",
        "Grid cells",
        "Preset",
        "Show cell values",
        "Show isoline labels",
        "First isoline [K]",
        "Isoline step [K]",
        "cmin",
        "cmax",
        "Map preset",
        "Map viewport [lon_min,lon_max,lat_min,lat_max]",
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
        "Export map SVG",
    ]:
        assert control in index


def test_default_combined_plot_uses_filled_contour_layer() -> None:
    app_data = build_visualization_data("web/public/data")

    figure = build_dash_figure(app_data, app_data["defaults"])

    assert [trace.type for trace in figure.data] == ["contour", "contour"]
    assert figure.data[0].contours.coloring == "heatmap"
    assert figure.data[0].contours.showlines is False
    assert figure.data[0].showscale is True
    assert figure.data[0].zmin == 0
    assert figure.data[0].zmax == 16
    assert figure.data[1].zmin is None
    assert figure.data[1].zmax is None
    assert figure.data[1].autocontour is False
    assert figure.data[1].contours.coloring == "none"
    assert figure.data[1].contours.showlines is True
    assert figure.data[1].contours.start == 0
    assert figure.data[1].contours.size == 1
    assert list(figure.layout.xaxis.tickvals) == list(range(0, 24, 2))
    assert figure.layout.xaxis.tickangle == 0
    assert list(figure.layout.yaxis.ticktext) == [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    assert "Climatology" not in figure.layout.title.text
    assert figure.layout.title.text.startswith("<b>")
    assert "Wetbulb Potential" in figure.layout.title.text
    selected_location = next(
        location
        for location in app_data["locations"]
        if location["id"] == app_data["defaults"]["location"]
    )
    assert selected_location["name"] in figure.layout.title.text
    assert selected_location["country"] in figure.layout.title.text
    assert "<br>" in figure.layout.title.text
    assert figure.data[0].colorbar.title.text == "ΔT [K]"
    assert figure.data[0].colorbar.title.side == "right"
    assert figure.layout.annotations[0].text == (
        f"Data Source: {app_data['defaults']['source']} "
        f"{app_data['defaults']['yearStart']}-{app_data['defaults']['yearEnd']}"
    )
    assert figure.layout.margin.b >= 90
    assert figure.layout.annotations[0].y <= -0.3


def test_grid_color_fill_mode_uses_heatmap_layer() -> None:
    app_data = build_visualization_data("web/public/data")
    settings = dict(app_data["defaults"])
    settings["colorFillMode"] = "grid"

    figure = build_dash_figure(app_data, settings)

    assert [trace.type for trace in figure.data] == ["heatmap", "contour"]
    assert figure.data[0].zmin == 0
    assert figure.data[0].zmax == 16
    assert figure.data[1].contours.start == 0
    assert figure.data[1].contours.size == 1


def test_dash_location_map_uses_locations_and_selection() -> None:
    app_data = build_visualization_data("web/public/data")
    defaults = app_data["defaults"]

    figure = build_location_map_figure(app_data, defaults["source"], defaults["location"])

    assert [trace.type for trace in figure.data] == ["scattergeo"]
    assert list(figure.data[0].customdata) == [location["id"] for location in app_data["locations"]]
    assert list(figure.data[0].lat) == [location["latitude"] for location in app_data["locations"]]
    assert list(figure.data[0].lon) == [location["longitude"] for location in app_data["locations"]]
    assert all("<strong>" not in text for text in figure.data[0].text)
    assert "#b3261e" in list(figure.data[0].marker.color)
    assert figure.layout.geo.scope == "world"
    assert figure.layout.uirevision == "location-map"


def test_dash_location_click_prefers_available_current_metric() -> None:
    app_data = {
        "availability": [
            {
                "source": "NASA_POWER",
                "location_id": "phoenix",
                "metric": "pressure_hpa",
                "year_min": 2002,
                "year_max": 2013,
            },
            {
                "source": "NOAA",
                "location_id": "phoenix",
                "metric": "delta_t_k",
                "year_min": 2005,
                "year_max": 2010,
            },
        ]
    }

    availability = preferred_availability_for_location(
        app_data,
        "phoenix",
        "NOAA",
        "pressure_hpa",
    )

    assert availability == {
        "source": "NOAA",
        "location_id": "phoenix",
        "metric": "delta_t_k",
        "year_min": 2005,
        "year_max": 2010,
    }
