# ruff: noqa: E501

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .visualization import build_visualization_data


def build_site(data_dir: str | Path, out_dir: str | Path) -> None:
    out_path = Path(out_dir)
    assets_path = out_path / "assets"
    if out_path.exists():
        shutil.rmtree(out_path)
    assets_path.mkdir(parents=True, exist_ok=True)

    data = build_visualization_data(data_dir)
    (assets_path / "data.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (out_path / "index.html").write_text(_index_html(), encoding="utf-8")
    (out_path / ".nojekyll").write_text("", encoding="utf-8")


def _index_html() -> str:
    return r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Wetbulb Potential</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
      :root {
        color: #17202e;
        background: #f5f7fa;
        font-family: Arial, sans-serif;
      }
      * { box-sizing: border-box; }
      body { margin: 0; }
      main {
        min-height: 100vh;
        display: grid;
        grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
        gap: 14px;
        padding: 14px;
      }
      .settings, .figure-area {
        background: #fff;
        border: 1px solid #cfd7e3;
        border-radius: 8px;
      }
      .source-box {
        grid-column: 1 / -1;
        background: #fff;
        border: 1px solid #cfd7e3;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 13px;
      }
      .source-box a { color: #174ea6; }
      .settings {
        padding: 10px;
        display: grid;
        gap: 10px;
        align-content: start;
      }
      .panel {
        border: 1px solid #d9e0ea;
        border-radius: 8px;
        padding: 10px;
      }
      .panel h2 {
        margin: 0 0 9px;
        font-size: 14px;
        letter-spacing: 0;
      }
      .note {
        margin-top: 8px;
        color: #17202e;
        font-size: 12px;
        font-weight: 700;
      }
      label {
        display: grid;
        gap: 4px;
        margin: 7px 0;
        color: #4a5870;
        font-size: 12px;
        font-weight: 600;
      }
      select, input {
        width: 100%;
        min-height: 30px;
        border: 1px solid #b8c3d2;
        border-radius: 6px;
        padding: 4px 7px;
        color: #17202e;
        background: #fff;
      }
      .check-row {
        grid-template-columns: auto 1fr;
        align-items: center;
      }
      .check-row input { width: 16px; min-height: 16px; }
      button {
        width: 100%;
        min-height: 32px;
        border: 1px solid #17202e;
        border-radius: 6px;
        background: #17202e;
        color: #fff;
        cursor: pointer;
      }
      .figure-area {
        display: grid;
        grid-template-rows: minmax(420px, auto) auto;
        overflow: hidden;
      }
      #plot { width: 100%; min-height: 420px; }
      .method {
        border-top: 1px solid #d9e0ea;
        padding: 12px;
        font-size: 13px;
        color: #39485d;
      }
      .method strong { color: #17202e; }
      @media (max-width: 980px) {
        main { grid-template-columns: 1fr; }
        .source-box { grid-column: auto; }
      }
    </style>
  </head>
  <body>
    <template id="required-controls">
      Analysis Percentiles Lines & Legend Figure & Export Plot mode X axis Y axis Line color
      Legend entries Display Legend Line shape Percentile dash Legend position Line width
      Marker size Opacity Figure title Font family Figure width [px] Figure height [px]
      Base font size Title font size Axis title font size Tick font size Legend font size
      SAE options Show title Cycle line styles Export SVG
    </template>
    <main>
      <section class="source-box" id="sourceBox"></section>
      <aside class="settings" id="settings"></aside>
      <section class="figure-area">
        <div id="plot"></div>
        <div class="method" id="methodBox"></div>
      </section>
    </main>
    <script>
      const DASHES = ['solid', 'dash', 'dot', 'dashdot'];
      const COLORS = ['#174ea6', '#b3261e', '#0b8043', '#7b1fa2', '#f29900', '#00838f'];

      let appData;
      let state;

      fetch('assets/data.json')
        .then((response) => response.json())
        .then((data) => {
          appData = data;
          state = { ...data.defaults };
          renderSourceBox();
          renderSettings();
          updatePlot();
        });

      function renderSourceBox() {
        const links = appData.sourceNote.links
          .map((link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${link.label}</a>`)
          .join(' · ');
        document.getElementById('sourceBox').innerHTML =
          `<strong>Sources:</strong> ${links}`;
        document.getElementById('methodBox').innerHTML =
          `<strong>${appData.sourceNote.title}.</strong> ${appData.sourceNote.html}`;
      }

      function renderSettings() {
        const settings = document.getElementById('settings');
        settings.innerHTML = '';
        for (const panel of appData.panels) {
          const section = document.createElement('section');
          section.className = 'panel';
          section.innerHTML = `<h2>${panel.title}</h2>`;
          for (const control of panel.controls) {
            section.appendChild(renderControl(control));
          }
          settings.appendChild(section);
        }
        refreshDependentOptions();
      }

      function renderControl(control) {
        if (control.type === 'button') {
          const button = document.createElement('button');
          button.id = control.id;
          button.textContent = control.label;
          button.addEventListener('click', () => {
            Plotly.downloadImage('plot', {
              format: 'svg',
              filename: 'wetbulb-potential',
              width: Number(state.figureWidth),
              height: Number(state.figureHeight)
            });
          });
          return button;
        }
        if (control.type === 'note') {
          const note = document.createElement('div');
          note.className = 'note';
          note.textContent = control.label;
          return note;
        }
        const label = document.createElement('label');
        label.textContent = control.label;
        if (control.type === 'checkbox') {
          label.className = 'check-row';
          const input = document.createElement('input');
          input.id = control.id;
          input.type = 'checkbox';
          input.checked = Boolean(state[control.id]);
          input.addEventListener('change', () => {
            state[control.id] = input.checked;
            updatePlot();
          });
          label.prepend(input);
          return label;
        }
        const input = document.createElement(control.type === 'select' ? 'select' : 'input');
        input.id = control.id;
        if (control.type !== 'select') {
          input.type = control.type;
          input.value = state[control.id] ?? '';
          if (control.type === 'number') input.step = '0.1';
        }
        if (control.options) fillOptions(input, control.options);
        input.addEventListener('input', () => {
          state[control.id] = control.type === 'number' ? Number(input.value) : input.value;
          refreshDependentOptions();
          updatePlot();
        });
        label.appendChild(input);
        return label;
      }

      function fillOptions(select, options) {
        select.innerHTML = '';
        for (const option of options) {
          const node = document.createElement('option');
          node.value = option.id ?? option;
          node.textContent = option.label ?? option;
          select.appendChild(node);
        }
        select.value = state[select.id] ?? select.options[0]?.value ?? '';
      }

      function refreshDependentOptions() {
        fillOptions(document.getElementById('xAxis'), appData.axes.x);
        fillOptions(document.getElementById('yAxis'), appData.axes.y);
        fillOptions(document.getElementById('lineColor'), appData.axes.lineColor);
        fillOptions(document.getElementById('source'), appData.sources.map((item) => ({ id: item.id, label: item.label })));
        fillOptions(document.getElementById('location'), appData.locations.map((item) => ({ id: item.id, label: item.name })));
        fillOptions(document.getElementById('metric'), appData.metrics.map((item) => ({ id: item.id, label: item.label })));
        const years = Array.from(new Set(appData.series.map((item) => item.year))).sort();
        fillOptions(document.getElementById('yearStart'), years);
        fillOptions(document.getElementById('yearEnd'), years);
      }

      function filteredSeries() {
        return appData.series.filter((item) =>
          item.source === state.source &&
          item.location === state.location &&
          item.metric === state.metric &&
          item.year >= Number(state.yearStart) &&
          item.year <= Number(state.yearEnd)
        );
      }

      function updatePlot() {
        const series = filteredSeries();
        const yKey = state.yAxis;
        const data = state.plotMode === 'Vehicles'
          ? vehicleTraces(series, yKey)
          : percentileTraces(series, yKey);
        Plotly.react('plot', data, layout(series), {
          responsive: true,
          displaylogo: false,
          toImageButtonOptions: {
            format: 'svg',
            filename: 'wetbulb-potential',
            width: Number(state.figureWidth),
            height: Number(state.figureHeight)
          }
        });
      }

      function vehicleTraces(series, yKey) {
        const groups = new Map();
        return series.map((item, index) => {
          const group = colorGroup(item);
          const seen = groups.has(group);
          groups.set(group, true);
          return {
            type: 'scatter',
            mode: Number(state.markerSize) > 0 ? 'lines+markers' : 'lines',
            name: group,
            legendgroup: group,
            showlegend: !seen,
            x: item.x,
            y: item[yKey],
            line: {
              color: COLORS[index % COLORS.length],
              width: Number(state.lineWidth),
              shape: lineShape()
            },
            marker: { size: Number(state.markerSize) },
            opacity: Number(state.opacity)
          };
        });
      }

      function percentileTraces(series, yKey) {
        const curves = computePercentiles(series, state.percentiles, yKey);
        if (state.percentileDisplay === 'Interpolated color field') {
          return [{
            type: 'contour',
            x: curves[0]?.x ?? [],
            y: curves.map((curve) => curve.percentile),
            z: curves.map((curve) => curve.y),
            colorscale: 'Viridis',
            contours: { coloring: 'heatmap', showlabels: true },
            colorbar: state.percentileLegend === 'Colorbar' ? { title: yAxisTitle() } : undefined,
            showscale: state.percentileLegend === 'Colorbar',
            hovertemplate: 'Hour %{x}<br>Percentile %{y}<br>Value %{z:.2f}<extra></extra>'
          }];
        }
        const legendTokens = new Set(parsePercentiles(state.legendEntries).map((item) => item.token));
        const visibleCurves = [...curves].reverse();
        return visibleCurves.map((curve, index) => ({
          type: 'scatter',
          mode: Number(state.markerSize) > 0 ? 'lines+markers' : 'lines',
          name: curve.label,
          x: curve.x,
          y: curve.y,
          showlegend: state.percentileLegend === 'Legend entries' && legendTokens.has(curve.token),
          line: {
            color: percentileColor(curve.percentile),
            width: Number(state.lineWidth),
            dash: percentileDash(index),
            shape: lineShape()
          },
          marker: { size: Number(state.markerSize) },
          opacity: Number(state.opacity)
        }));
      }

      function layout(series) {
        const title = state.showTitle ? `<b>${state.figureTitle}</b>` : '';
        return {
          width: Number(state.figureWidth),
          height: Number(state.figureHeight),
          title: {
            text: title,
            x: 0.5,
            xanchor: 'center',
            font: { size: Number(state.titleFontSize), family: state.fontFamily }
          },
          paper_bgcolor: '#ffffff',
          plot_bgcolor: '#ffffff',
          font: {
            family: state.fontFamily,
            size: Number(state.baseFontSize),
            color: '#17202e'
          },
          xaxis: {
            title: { text: xAxisTitle(), font: { size: Number(state.axisTitleFontSize) } },
            tickfont: { size: Number(state.tickFontSize) },
            gridcolor: '#d9dde5',
            linecolor: '#000000',
            zeroline: false
          },
          yaxis: {
            title: { text: yAxisTitle(series), font: { size: Number(state.axisTitleFontSize) } },
            tickfont: { size: Number(state.tickFontSize) },
            gridcolor: '#d9dde5',
            linecolor: '#000000',
            zeroline: false
          },
          legend: legendLayout(),
          margin: { l: 70, r: 20, t: state.showTitle ? 55 : 20, b: 60 }
        };
      }

      function xAxisTitle() {
        return appData.axes.x.find((item) => item.id === state.xAxis)?.label ?? 'Local hour [h]';
      }

      function yAxisTitle(series) {
        if (state.yAxis === 'relative_value') return 'Relative wetbulb spread [%]';
        const metric = appData.metrics.find((item) => item.id === state.metric);
        return metric ? `${metric.label} [${metric.unit}]` : 'Value';
      }

      function colorGroup(item) {
        if (state.lineColor === 'month') return item.monthLabel;
        if (state.lineColor === 'year') return String(item.year);
        if (state.lineColor === 'source') return item.source;
        if (state.lineColor === 'location') return item.locationLabel;
        return item.label;
      }

      function lineShape() {
        if (state.lineShape === 'step hv') return 'hv';
        if (state.lineShape === 'step vh') return 'vh';
        if (state.lineShape === 'smoothed') return 'spline';
        return 'linear';
      }

      function percentileDash(index) {
        if (state.percentileDash === 'Cycle line styles' || state.cycleLineStyles) {
          return DASHES[index % DASHES.length];
        }
        const map = { Solid: 'solid', Dash: 'dash', Dot: 'dot', 'Dash-dot': 'dashdot' };
        return map[state.percentileDash] ?? 'solid';
      }

      function percentileColor(percentile) {
        const hue = 220 - (percentile / 100) * 200;
        return `hsl(${hue}, 70%, 40%)`;
      }

      function legendLayout() {
        const base = { font: { size: Number(state.legendFontSize), family: state.fontFamily } };
        const position = state.legendPosition;
        if (position === 'Top') return { ...base, orientation: 'h', x: 0.5, y: 1.15, xanchor: 'center' };
        if (position === 'Bottom') return { ...base, orientation: 'h', x: 0.5, y: -0.22, xanchor: 'center' };
        if (position === 'Right') return { ...base, x: 1.02, y: 1, xanchor: 'left' };
        if (position === 'Inside bottom left') return { ...base, x: 0.02, y: 0.02 };
        if (position === 'Inside bottom right') return { ...base, x: 0.98, y: 0.02, xanchor: 'right' };
        return { ...base, x: 0.98, y: 0.98, xanchor: 'right' };
      }

      function parsePercentiles(text) {
        return text.split(',').map((token) => token.trim()).filter(Boolean).map((token) => {
          if (token.toLowerCase() === 'worst') return { token: 'Worst', percentile: 0, label: 'Worst' };
          if (token.toLowerCase() === 'top') return { token: 'Top', percentile: 100, label: 'Top' };
          const value = Number(token.replace('%', '').trim());
          return { token, percentile: value, label: `${value}% Percentile` };
        });
      }

      function computePercentiles(series, text, yKey) {
        const specs = parsePercentiles(text);
        const xGrid = [...new Set(series.flatMap((item) => item.x))].sort((a, b) => a - b);
        const interpolated = series.map((item) => interpolate(item.x, item[yKey], xGrid));
        return specs.map((spec) => ({
          ...spec,
          x: xGrid,
          y: xGrid.map((_, column) => percentile(interpolated.map((row) => row[column]), spec.percentile))
        }));
      }

      function interpolate(x, y, grid) {
        const pairs = x.map((value, index) => [Number(value), y[index]])
          .filter((pair) => pair[1] !== null && pair[1] !== undefined && !Number.isNaN(pair[1]))
          .sort((a, b) => a[0] - b[0]);
        if (!pairs.length) return grid.map(() => NaN);
        if (pairs.length === 1) return grid.map(() => pairs[0][1]);
        return grid.map((target) => {
          if (target <= pairs[0][0]) return pairs[0][1];
          if (target >= pairs[pairs.length - 1][0]) return pairs[pairs.length - 1][1];
          for (let index = 1; index < pairs.length; index += 1) {
            if (pairs[index][0] >= target) {
              const [x0, y0] = pairs[index - 1];
              const [x1, y1] = pairs[index];
              const fraction = (target - x0) / (x1 - x0);
              return y0 * (1 - fraction) + y1 * fraction;
            }
          }
          return pairs[pairs.length - 1][1];
        });
      }

      function percentile(values, p) {
        const clean = values.filter((value) => value !== null && value !== undefined && !Number.isNaN(value)).sort((a, b) => a - b);
        if (!clean.length) return NaN;
        if (clean.length === 1) return clean[0];
        const rank = (p / 100) * (clean.length - 1);
        const low = Math.floor(rank);
        const high = Math.ceil(rank);
        if (low === high) return clean[low];
        const fraction = rank - low;
        return clean[low] * (1 - fraction) + clean[high] * fraction;
      }
    </script>
  </body>
</html>
"""
