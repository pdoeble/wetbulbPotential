from __future__ import annotations

from typing import Any

from .visualization import build_visualization_data, compute_percentile_curves


def create_dash_app(data_dir: str = "web/public/data"):
    from dash import Dash, Input, Output, dcc, html

    app_data = build_visualization_data(data_dir)
    defaults = app_data["defaults"]
    app = Dash(__name__)

    app.layout = html.Main(
        [
            html.Section(
                [
                    html.Strong("Sources: "),
                    *[
                        html.A(
                            link["label"],
                            href=link["url"],
                            target="_blank",
                            rel="noreferrer",
                            style={"marginRight": "10px"},
                        )
                        for link in app_data["sourceNote"]["links"]
                    ],
                ],
                className="source-box",
            ),
            html.Aside(_settings_layout(app_data), className="settings"),
            html.Section(
                [
                    dcc.Graph(
                        id="plot",
                        config={
                            "displaylogo": False,
                            "toImageButtonOptions": {
                                "format": "svg",
                                "filename": "wetbulb-potential",
                                "width": defaults["figureWidth"],
                                "height": defaults["figureHeight"],
                            },
                        },
                    ),
                    html.Div(
                        [
                            html.Strong(f"{app_data['sourceNote']['title']}. "),
                            dcc.Markdown(
                                app_data["sourceNote"]["html"],
                                dangerously_allow_html=True,
                            ),
                        ],
                        className="method",
                    ),
                ],
                className="figure-area",
            ),
        ],
        className="dash-app",
        style={
            "display": "grid",
            "gridTemplateColumns": "minmax(300px, 380px) minmax(0, 1fr)",
            "gap": "14px",
            "padding": "14px",
            "background": "#f5f7fa",
        },
    )

    @app.callback(
        Output("plot", "figure"),
        [
            Input("plotMode", "value"),
            Input("xAxis", "value"),
            Input("yAxis", "value"),
            Input("lineColor", "value"),
            Input("source", "value"),
            Input("location", "value"),
            Input("metric", "value"),
            Input("yearStart", "value"),
            Input("yearEnd", "value"),
            Input("percentiles", "value"),
            Input("legendEntries", "value"),
            Input("percentileDisplay", "value"),
            Input("percentileLegend", "value"),
            Input("lineShape", "value"),
            Input("percentileDash", "value"),
            Input("legendPosition", "value"),
            Input("lineWidth", "value"),
            Input("markerSize", "value"),
            Input("opacity", "value"),
            Input("figureTitle", "value"),
            Input("fontFamily", "value"),
            Input("figureWidth", "value"),
            Input("figureHeight", "value"),
            Input("baseFontSize", "value"),
            Input("titleFontSize", "value"),
            Input("axisTitleFontSize", "value"),
            Input("tickFontSize", "value"),
            Input("legendFontSize", "value"),
            Input("showTitle", "value"),
            Input("cycleLineStyles", "value"),
        ],
    )
    def _update_figure(*values):
        keys = [
            "plotMode",
            "xAxis",
            "yAxis",
            "lineColor",
            "source",
            "location",
            "metric",
            "yearStart",
            "yearEnd",
            "percentiles",
            "legendEntries",
            "percentileDisplay",
            "percentileLegend",
            "lineShape",
            "percentileDash",
            "legendPosition",
            "lineWidth",
            "markerSize",
            "opacity",
            "figureTitle",
            "fontFamily",
            "figureWidth",
            "figureHeight",
            "baseFontSize",
            "titleFontSize",
            "axisTitleFontSize",
            "tickFontSize",
            "legendFontSize",
            "showTitle",
            "cycleLineStyles",
        ]
        settings = dict(zip(keys, values, strict=True))
        settings["showTitle"] = "Show title" in (settings["showTitle"] or [])
        settings["cycleLineStyles"] = "Cycle line styles" in (settings["cycleLineStyles"] or [])
        return build_dash_figure(app_data, settings)

    return app


def _settings_layout(app_data: dict[str, Any]) -> list:
    from dash import html

    defaults = app_data["defaults"]
    years = sorted({item["year"] for item in app_data["series"]})
    dynamic_options = {
        "xAxis": app_data["axes"]["x"],
        "yAxis": app_data["axes"]["y"],
        "lineColor": app_data["axes"]["lineColor"],
        "source": [{"id": item["id"], "label": item["label"]} for item in app_data["sources"]],
        "location": [{"id": item["id"], "label": item["name"]} for item in app_data["locations"]],
        "metric": [{"id": item["id"], "label": item["label"]} for item in app_data["metrics"]],
        "yearStart": [{"id": year, "label": str(year)} for year in years],
        "yearEnd": [{"id": year, "label": str(year)} for year in years],
    }
    sections = []
    for panel in app_data["panels"]:
        children = [html.H2(panel["title"])]
        for control in panel["controls"]:
            children.append(_dash_control(control, defaults, dynamic_options))
        sections.append(html.Section(children, className="panel"))
    return sections


def _dash_control(
    control: dict[str, Any],
    defaults: dict[str, Any],
    dynamic_options: dict[str, Any],
):
    from dash import dcc, html

    control_id = control["id"]
    label = control["label"]
    if control["type"] == "button":
        return html.Button(label, id=control_id)
    if control["type"] == "note":
        return html.Div(label, className="note")
    if control["type"] == "checkbox":
        values = [label] if defaults.get(control_id) else []
        return html.Label([dcc.Checklist([label], values, id=control_id)])
    if control["type"] == "select":
        options = control.get("options") or dynamic_options.get(control_id, [])
        dash_options = [
            {"label": option.get("label", option.get("id")), "value": option.get("id")}
            if isinstance(option, dict)
            else {"label": option, "value": option}
            for option in options
        ]
        return html.Label(
            [label, dcc.Dropdown(dash_options, defaults.get(control_id), id=control_id)]
        )
    input_type = "number" if control["type"] == "number" else "text"
    return html.Label(
        [label, dcc.Input(id=control_id, type=input_type, value=defaults.get(control_id))]
    )


def build_dash_figure(app_data: dict[str, Any], settings: dict[str, Any]):
    import plotly.graph_objects as go

    series = [
        item
        for item in app_data["series"]
        if item["source"] == settings["source"]
        and item["location"] == settings["location"]
        and item["metric"] == settings["metric"]
        and int(settings["yearStart"]) <= item["year"] <= int(settings["yearEnd"])
    ]
    fig = go.Figure()
    if settings["plotMode"] == "Vehicles":
        for item in series:
            fig.add_trace(
                go.Scatter(
                    x=item["x"],
                    y=item[settings["yAxis"]],
                    mode="lines+markers" if float(settings["markerSize"]) > 0 else "lines",
                    name=_group_label(item, settings["lineColor"]),
                    legendgroup=_group_label(item, settings["lineColor"]),
                    line={
                        "width": float(settings["lineWidth"]),
                        "shape": _line_shape(settings["lineShape"]),
                    },
                    marker={"size": float(settings["markerSize"])},
                    opacity=float(settings["opacity"]),
                    showlegend=True,
                )
            )
    else:
        curves = compute_percentile_curves(series, settings["percentiles"], settings["yAxis"])
        if settings["percentileDisplay"] == "Interpolated color field":
            fig.add_trace(
                go.Contour(
                    x=curves[0]["x"] if curves else [],
                    y=[curve["percentile"] for curve in curves],
                    z=[curve["y"] for curve in curves],
                    colorscale="Viridis",
                    contours={"coloring": "heatmap", "showlabels": True},
                    showscale=settings["percentileLegend"] == "Colorbar",
                )
            )
        else:
            for index, curve in enumerate(reversed(curves)):
                fig.add_trace(
                    go.Scatter(
                        x=curve["x"],
                        y=curve["y"],
                        mode="lines+markers" if float(settings["markerSize"]) > 0 else "lines",
                        name=curve["label"],
                        line={
                            "width": float(settings["lineWidth"]),
                            "dash": _dash(settings, index),
                            "shape": _line_shape(settings["lineShape"]),
                        },
                        marker={"size": float(settings["markerSize"])},
                        opacity=float(settings["opacity"]),
                    )
                )

    fig.update_layout(
        width=int(settings["figureWidth"]),
        height=int(settings["figureHeight"]),
        title={
            "text": f"<b>{settings['figureTitle']}</b>" if settings["showTitle"] else "",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": int(settings["titleFontSize"])},
        },
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": settings["fontFamily"], "size": int(settings["baseFontSize"])},
        xaxis={
            "title": {
                "text": "Local hour [h]",
                "font": {"size": int(settings["axisTitleFontSize"])},
            },
            "tickfont": {"size": int(settings["tickFontSize"])},
            "gridcolor": "#d9dde5",
            "linecolor": "black",
            "zeroline": False,
        },
        yaxis={
            "title": {
                "text": _y_axis_title(app_data, settings),
                "font": {"size": int(settings["axisTitleFontSize"])},
            },
            "tickfont": {"size": int(settings["tickFontSize"])},
            "gridcolor": "#d9dde5",
            "linecolor": "black",
            "zeroline": False,
        },
        legend=_legend_position(settings["legendPosition"], int(settings["legendFontSize"])),
    )
    return fig


def _group_label(item: dict[str, Any], line_color: str) -> str:
    if line_color == "month":
        return item["monthLabel"]
    if line_color == "year":
        return str(item["year"])
    if line_color == "source":
        return item["source"]
    if line_color == "location":
        return item["locationLabel"]
    return item["label"]


def _line_shape(value: str) -> str:
    if value == "step hv":
        return "hv"
    if value == "step vh":
        return "vh"
    if value == "smoothed":
        return "spline"
    return "linear"


def _dash(settings: dict[str, Any], index: int) -> str:
    if settings["percentileDash"] == "Cycle line styles" or settings["cycleLineStyles"]:
        return ["solid", "dash", "dot", "dashdot"][index % 4]
    return {
        "Solid": "solid",
        "Dash": "dash",
        "Dot": "dot",
        "Dash-dot": "dashdot",
    }.get(settings["percentileDash"], "solid")


def _y_axis_title(app_data: dict[str, Any], settings: dict[str, Any]) -> str:
    if settings["yAxis"] == "relative_value":
        return "Relative wetbulb spread [%]"
    metric = next(item for item in app_data["metrics"] if item["id"] == settings["metric"])
    return f"{metric['label']} [{metric['unit']}]"


def _legend_position(position: str, font_size: int) -> dict[str, Any]:
    base: dict[str, Any] = {"font": {"size": font_size}}
    if position == "Top":
        return {**base, "orientation": "h", "x": 0.5, "y": 1.15, "xanchor": "center"}
    if position == "Bottom":
        return {**base, "orientation": "h", "x": 0.5, "y": -0.22, "xanchor": "center"}
    if position == "Right":
        return {**base, "x": 1.02, "y": 1, "xanchor": "left"}
    if position == "Inside bottom left":
        return {**base, "x": 0.02, "y": 0.02}
    if position == "Inside bottom right":
        return {**base, "x": 0.98, "y": 0.02, "xanchor": "right"}
    return {**base, "x": 0.98, "y": 0.98, "xanchor": "right"}


def run_dash(data_dir: str, host: str, port: int, debug: bool = False) -> None:
    app = create_dash_app(data_dir)
    app.run(host=host, port=port, debug=debug)
