from __future__ import annotations

from typing import Any

from .visualization import build_matrix, build_visualization_data

HOURS = list(range(24))
MONTHS = list(range(1, 13))
COLORSCALE = [
    [0, "#2451a6"],
    [0.25, "#2aa7a2"],
    [0.5, "#f1d46b"],
    [0.75, "#ec8f3c"],
    [1, "#a83232"],
]


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
                style=_box_style(),
            ),
            html.Aside(
                _settings_layout(app_data),
                className="settings",
                style={
                    **_box_style(),
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(230px, 1fr))",
                    "gap": "10px",
                    "padding": "10px",
                },
            ),
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
                ],
                className="figure-area",
                style=_box_style(),
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
                style={**_box_style(), "padding": "12px", "fontSize": "13px"},
            ),
        ],
        className="dash-app",
        style={
            "display": "grid",
            "gridTemplateRows": "auto auto minmax(460px, 1fr) auto",
            "gap": "14px",
            "padding": "14px",
            "background": "#f5f7fa",
            "minHeight": "100vh",
        },
    )

    @app.callback(
        Output("plot", "figure"),
        [
            Input("source", "value"),
            Input("location", "value"),
            Input("metric", "value"),
            Input("yearStart", "value"),
            Input("yearEnd", "value"),
            Input("plotType", "value"),
            Input("preset", "value"),
            Input("showValues", "value"),
            Input("showContourLabels", "value"),
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
        ],
    )
    def _update_figure(*values):
        keys = [
            "source",
            "location",
            "metric",
            "yearStart",
            "yearEnd",
            "plotType",
            "preset",
            "showValues",
            "showContourLabels",
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
        ]
        settings = dict(zip(keys, values, strict=True))
        settings["showValues"] = "Show cell values" in (settings["showValues"] or [])
        settings["showContourLabels"] = "Show isoline labels" in (
            settings["showContourLabels"] or []
        )
        settings["showTitle"] = "Show title" in (settings["showTitle"] or [])
        return build_dash_figure(app_data, settings)

    return app


def _settings_layout(app_data: dict[str, Any]) -> list:
    from dash import html

    defaults = app_data["defaults"]
    years = sorted({item["year"] for item in app_data["cells"]})
    dynamic_options = {
        "source": [{"id": item["id"], "label": item["label"]} for item in app_data["sources"]],
        "location": [{"id": item["id"], "label": item["name"]} for item in app_data["locations"]],
        "metric": [{"id": item["id"], "label": item["label"]} for item in app_data["metrics"]],
        "yearStart": [{"id": year, "label": str(year)} for year in years],
        "yearEnd": [{"id": year, "label": str(year)} for year in years],
        "plotType": app_data["plotTypes"],
    }
    sections = []
    for panel in app_data["panels"]:
        children = [html.H2(panel["title"], style={"fontSize": "14px", "margin": "0 0 9px"})]
        for control in panel["controls"]:
            children.append(_dash_control(control, defaults, dynamic_options))
        sections.append(
            html.Section(
                children,
                className="panel",
                style={"border": "1px solid #d9e0ea", "borderRadius": "8px", "padding": "10px"},
            )
        )
    return sections


def _dash_control(
    control: dict[str, Any],
    defaults: dict[str, Any],
    dynamic_options: dict[str, Any],
):
    from dash import dcc, html

    control_id = control["id"]
    label = control["label"]
    label_style = {
        "display": "grid",
        "gap": "4px",
        "margin": "7px 0",
        "fontSize": "12px",
        "fontWeight": "600",
        "color": "#4a5870",
    }
    if control["type"] == "button":
        return html.Button(label, id=control_id, style={"width": "100%", "minHeight": "32px"})
    if control["type"] == "checkbox":
        values = [label] if defaults.get(control_id) else []
        return html.Label([dcc.Checklist([label], values, id=control_id)], style=label_style)
    if control["type"] == "select":
        options = control.get("options") or dynamic_options.get(control_id, [])
        dash_options = [
            {"label": option.get("label", option.get("id")), "value": option.get("id")}
            if isinstance(option, dict)
            else {"label": option, "value": option}
            for option in options
        ]
        return html.Label(
            [label, dcc.Dropdown(dash_options, defaults.get(control_id), id=control_id)],
            style=label_style,
        )
    input_type = "number" if control["type"] == "number" else "text"
    return html.Label(
        [label, dcc.Input(id=control_id, type=input_type, value=defaults.get(control_id))],
        style=label_style,
    )


def build_dash_figure(app_data: dict[str, Any], settings: dict[str, Any]):
    import plotly.graph_objects as go

    metric = _metric(app_data, settings["metric"])
    matrix = build_matrix(
        app_data["cells"],
        settings["source"],
        settings["location"],
        settings["metric"],
        int(settings["yearStart"]),
        int(settings["yearEnd"]),
    )
    fig = go.Figure()
    if settings["plotType"] == "heatmap":
        fig.add_trace(
            go.Heatmap(
                x=HOURS,
                y=MONTHS,
                z=matrix,
                colorscale=COLORSCALE,
                colorbar={"title": {"text": metric["unit"]}},
                hovertemplate=(
                    "Month %{y}<br>Hour %{x}:00<br>"
                    f"{metric['label']} %{{z:.2f}} {metric['unit']}<extra></extra>"
                ),
                text=_cell_text(matrix) if settings["showValues"] else None,
                texttemplate="%{text}" if settings["showValues"] else None,
                textfont={"size": max(8, int(settings["tickFontSize"]) - 4)},
            )
        )
    elif settings["plotType"] == "combined":
        fig.add_trace(
            go.Contour(
                x=HOURS,
                y=MONTHS,
                z=matrix,
                colorscale=COLORSCALE,
                colorbar={"title": {"text": metric["unit"]}},
                contours={
                    "coloring": "heatmap",
                    "showlabels": settings["showContourLabels"],
                    "showlines": True,
                },
                line={
                    "color": "#111827",
                    "width": 1.1 if settings["preset"] == "sae" else 0.9,
                },
                showscale=True,
                hovertemplate=(
                    "Month %{y}<br>Hour %{x}:00<br>"
                    f"{metric['label']} %{{z:.2f}} {metric['unit']}<extra></extra>"
                ),
            )
        )
        if settings["showValues"]:
            fig.add_trace(_cell_value_trace(matrix, settings))
    else:
        fig.add_trace(
            go.Contour(
                x=HOURS,
                y=MONTHS,
                z=matrix,
                contours={
                    "coloring": "none",
                    "showlabels": settings["showContourLabels"],
                    "showlines": True,
                },
                line={"color": "#111827", "width": 1.1 if settings["preset"] == "sae" else 0.9},
                showscale=False,
                hovertemplate=(
                    "Month %{y}<br>Hour %{x}:00<br>"
                    f"{metric['label']} %{{z:.2f}} {metric['unit']}<extra></extra>"
                ),
            )
        )
        if settings["showValues"]:
            fig.add_trace(_cell_value_trace(matrix, settings))

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
            "tickmode": "array",
            "tickvals": HOURS,
            "tickfont": {"size": int(settings["tickFontSize"])},
            "gridcolor": "#d7dce3" if settings["preset"] == "sae" else "#edf0f4",
            "linecolor": "black",
            "zeroline": False,
        },
        yaxis={
            "title": {
                "text": "Month [-]",
                "font": {"size": int(settings["axisTitleFontSize"])},
            },
            "tickmode": "array",
            "tickvals": MONTHS,
            "autorange": "reversed",
            "tickfont": {"size": int(settings["tickFontSize"])},
            "gridcolor": "#d7dce3" if settings["preset"] == "sae" else "#edf0f4",
            "linecolor": "black",
            "zeroline": False,
        },
        margin={"l": 70, "r": 55, "t": 55 if settings["showTitle"] else 20, "b": 60},
        annotations=[
            {
                "text": (
                    f"{_location(app_data, settings['location'])['name']} · "
                    f"{settings['source']} · {metric['label']} [{metric['unit']}] · "
                    f"{settings['yearStart']}-{settings['yearEnd']}"
                ),
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.18,
                "showarrow": False,
                "xanchor": "left",
                "font": {"size": max(10, int(settings["legendFontSize"]) - 2), "color": "#4a5870"},
            }
        ],
    )
    return fig


def _cell_text(matrix: list[list[float | None]]) -> list[list[str]]:
    return [["" if value is None else f"{value:.2f}" for value in row] for row in matrix]


def _cell_value_trace(matrix: list[list[float | None]], settings: dict[str, Any]):
    import plotly.graph_objects as go

    x_values: list[int] = []
    y_values: list[int] = []
    text_values: list[str] = []
    for month_index, row in enumerate(matrix):
        for hour, value in enumerate(row):
            if value is None:
                continue
            x_values.append(hour)
            y_values.append(month_index + 1)
            text_values.append(f"{value:.2f}")
    return go.Scatter(
        x=x_values,
        y=y_values,
        text=text_values,
        mode="text",
        textfont={"size": max(8, int(settings["tickFontSize"]) - 4), "color": "#152033"},
        hoverinfo="skip",
        showlegend=False,
    )


def _metric(app_data: dict[str, Any], metric_id: str) -> dict[str, Any]:
    return next((item for item in app_data["metrics"] if item["id"] == metric_id), {})


def _location(app_data: dict[str, Any], location_id: str) -> dict[str, Any]:
    return next((item for item in app_data["locations"] if item["id"] == location_id), {})


def _box_style() -> dict[str, str]:
    return {
        "background": "#fff",
        "border": "1px solid #cfd7e3",
        "borderRadius": "8px",
    }


def run_dash(data_dir: str, host: str, port: int, debug: bool = False) -> None:
    app = create_dash_app(data_dir)
    app.run(host=host, port=port, debug=debug)
