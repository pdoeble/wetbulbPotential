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
        grid-template-rows: auto auto auto auto;
        gap: 14px;
        padding: 14px;
      }
      .source-box, .settings, .map-panel, .figure-area, .method {
        background: #fff;
        border: 1px solid #cfd7e3;
        border-radius: 8px;
      }
      .source-box {
        padding: 10px 12px;
        font-size: 13px;
      }
      .source-box a { color: #174ea6; }
      .visualization-grid {
        display: grid;
        grid-template-columns: minmax(340px, 0.85fr) minmax(520px, 1.15fr);
        gap: 14px;
        align-items: stretch;
      }
      .settings {
        padding: 10px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 10px;
        align-items: start;
      }
      .map-panel {
        min-height: 460px;
        display: grid;
        grid-template-rows: auto minmax(0, 1fr);
        overflow: hidden;
      }
      .map-panel h2 {
        margin: 0;
        padding: 10px 12px 0;
        font-size: 14px;
        letter-spacing: 0;
      }
      #locationMap {
        width: 100%;
        height: 100%;
        min-height: 420px;
      }
      .panel {
        border: 1px solid #d9e0ea;
        border-radius: 8px;
        padding: 10px;
        min-width: 0;
      }
      .panel h2 {
        margin: 0 0 9px;
        font-size: 14px;
        letter-spacing: 0;
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
        display: grid;
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
        overflow: hidden;
        min-height: 460px;
      }
      #plot { width: 100%; min-height: 460px; }
      .method {
        padding: 12px;
        font-size: 13px;
        color: #39485d;
      }
      .method strong { color: #17202e; }
      @media (max-width: 980px) {
        .visualization-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <template id="required-controls">
      Data Plot Figure & Export Data source Location Metric Year start Year end Display Preset
      Show cell values Show isoline labels Figure title Font family Figure width [px]
      Figure height [px] Base font size Title font size Axis title font size Tick font size
      Legend font size Show title Export SVG Heatmap Isolines Heatmap + isolines Locations
    </template>
    <main>
      <section class="source-box" id="sourceBox"></section>
      <section class="visualization-grid">
        <section class="map-panel">
          <h2>Locations</h2>
          <div id="locationMap"></div>
        </section>
        <section class="figure-area">
          <div id="plot"></div>
        </section>
      </section>
      <aside class="settings" id="settings"></aside>
      <div class="method" id="methodBox"></div>
    </main>
    <script>
      const HOURS = Array.from({ length: 24 }, (_, index) => index);
      const MONTHS = Array.from({ length: 12 }, (_, index) => index + 1);
      const COLORSCALE = [
        [0, '#2451a6'],
        [0.25, '#2aa7a2'],
        [0.5, '#f1d46b'],
        [0.75, '#ec8f3c'],
        [1, '#a83232']
      ];

      let appData;
      let state;

      fetch('assets/data.json')
        .then((response) => response.json())
        .then((data) => {
          appData = data;
          state = { ...data.defaults };
          renderSourceBox();
          renderSettings();
          refreshDependentOptions();
          updateLocationMap();
          updatePlot();
        });

      function renderSourceBox() {
        const links = appData.sourceNote.links
          .map((link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${link.label}</a>`)
          .join(' · ');
        document.getElementById('sourceBox').innerHTML = `<strong>Sources:</strong> ${links}`;
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
      }

      function renderControl(control) {
        if (control.type === 'button') {
          const button = document.createElement('button');
          button.id = control.id;
          button.textContent = control.label;
          button.addEventListener('click', exportPlotSvg);
          return button;
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
          if (control.type === 'number') input.step = '1';
        }
        if (control.options) fillOptions(input, control.options);
        input.addEventListener('input', () => {
          state[control.id] = control.type === 'number' ? Number(input.value) : input.value;
          refreshDependentOptions();
          updateLocationMap();
          updatePlot();
        });
        label.appendChild(input);
        return label;
      }

      function refreshDependentOptions() {
        fillOptions(document.getElementById('source'), availableSources());
        fillOptions(document.getElementById('location'), availableLocations());
        fillOptions(document.getElementById('metric'), availableMetrics());
        fillOptions(document.getElementById('yearStart'), availableYears());
        fillOptions(document.getElementById('yearEnd'), availableYears());
        fillOptions(document.getElementById('plotType'), appData.plotTypes);
      }

      function fillOptions(select, options) {
        if (!select) return;
        const current = state[select.id];
        select.innerHTML = '';
        for (const option of options) {
          const node = document.createElement('option');
          node.value = option.id ?? option;
          node.textContent = option.label ?? option;
          select.appendChild(node);
        }
        const values = Array.from(select.options).map((option) => option.value);
        if (!values.includes(String(current))) {
          state[select.id] = select.options[0]?.value ?? '';
        }
        select.value = state[select.id] ?? '';
      }

      function availableSources() {
        const ids = [...new Set(appData.availability.map((item) => item.source))].sort();
        return ids.map((id) => ({ id, label: appData.sources.find((item) => item.id === id)?.label ?? id }));
      }

      function availableLocations() {
        const ids = new Set(appData.availability.filter((item) => item.source === state.source).map((item) => item.location_id));
        return appData.locations.filter((item) => ids.has(item.id)).map((item) => ({ id: item.id, label: item.name }));
      }

      function availableMetrics() {
        const ids = new Set(appData.availability.filter((item) => item.source === state.source && item.location_id === state.location).map((item) => item.metric));
        return appData.metrics.filter((item) => ids.has(item.id)).map((item) => ({ id: item.id, label: item.label }));
      }

      function availableYears() {
        const availability = appData.availability.find((item) =>
          item.source === state.source && item.location_id === state.location && item.metric === state.metric
        );
        if (!availability) return [];
        const years = [];
        for (let year = availability.year_min; year <= availability.year_max; year += 1) years.push(year);
        if (Number(state.yearStart) < availability.year_min || Number(state.yearStart) > availability.year_max) state.yearStart = availability.year_min;
        if (Number(state.yearEnd) < availability.year_min || Number(state.yearEnd) > availability.year_max) state.yearEnd = availability.year_max;
        return years;
      }

      function updateLocationMap() {
        const map = document.getElementById('locationMap');
        if (!map || !appData.locations.length) return;
        const currentSourceLocations = new Set(
          appData.availability
            .filter((item) => item.source === state.source)
            .map((item) => item.location_id)
        );
        const markerColors = appData.locations.map((item) => {
          if (item.id === state.location) return '#b3261e';
          return currentSourceLocations.has(item.id) ? '#174ea6' : '#8c98a9';
        });
        const markerSizes = appData.locations.map((item) => item.id === state.location ? 12 : 7);
        const markerOpacity = appData.locations.map((item) =>
          item.id === state.location || currentSourceLocations.has(item.id) ? 1 : 0.55
        );
        Plotly.react('locationMap', [{
          type: 'scattergeo',
          mode: 'markers',
          lat: appData.locations.map((item) => item.latitude),
          lon: appData.locations.map((item) => item.longitude),
          text: appData.locations.map((item) => locationMapLabel(item)),
          customdata: appData.locations.map((item) => item.id),
          marker: {
            size: markerSizes,
            color: markerColors,
            opacity: markerOpacity,
            line: { color: '#ffffff', width: 1 }
          },
          hovertemplate: '%{text}<extra></extra>'
        }], {
          geo: {
            scope: 'world',
            projection: { type: 'natural earth' },
            showframe: false,
            showland: true,
            landcolor: '#edf2f7',
            showcountries: true,
            countrycolor: '#c7d0dd',
            showcoastlines: true,
            coastlinecolor: '#b9c4d3',
            showocean: true,
            oceancolor: '#ffffff',
            bgcolor: '#ffffff'
          },
          margin: { l: 0, r: 0, t: 0, b: 0 },
          paper_bgcolor: '#ffffff',
          plot_bgcolor: '#ffffff'
        }, {
          responsive: true,
          displayModeBar: false
        });
        if (!map.dataset.clickHandlerAttached) {
          map.on('plotly_click', (event) => {
            const locationId = event.points?.[0]?.customdata;
            if (locationId) selectLocationFromMap(locationId);
          });
          map.dataset.clickHandlerAttached = 'true';
        }
      }

      function locationMapLabel(location) {
        const rows = [`<strong>${location.name}</strong>`, location.country];
        if (location.climate_label) rows.push(location.climate_label);
        if (location.elevation_m !== null && location.elevation_m !== undefined) {
          rows.push(`${Number(location.elevation_m).toFixed(0)} m`);
        }
        return rows.join('<br>');
      }

      function selectLocationFromMap(locationId) {
        const availability = preferredAvailabilityForLocation(locationId);
        if (!availability) return;
        state.source = availability.source;
        state.location = availability.location_id;
        state.metric = availability.metric;
        state.yearStart = availability.year_min;
        state.yearEnd = availability.year_max;
        refreshDependentOptions();
        updateLocationMap();
        updatePlot();
      }

      function preferredAvailabilityForLocation(locationId) {
        const options = appData.availability.filter((item) => item.location_id === locationId);
        return (
          options.find((item) => item.source === state.source && item.metric === state.metric) ||
          options.find((item) => item.source === state.source && item.metric === 'delta_t_k') ||
          options.find((item) => item.metric === state.metric) ||
          options.find((item) => item.metric === 'delta_t_k') ||
          options[0]
        );
      }

      function updatePlot() {
        const matrix = buildMatrix();
        Plotly.react('plot', plotData(matrix), layout(), {
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

      function exportPlotSvg() {
        const root = document.getElementById('plot');
        const plot = root?.querySelector('.js-plotly-plot') || root;
        if (!plot || !window.Plotly) return;
        Plotly.downloadImage(plot, {
          format: 'svg',
          filename: 'wetbulb-potential',
          width: Number(state.figureWidth) || 500,
          height: Number(state.figureHeight) || 400
        });
      }

      function buildMatrix() {
        const weighted = MONTHS.map(() => HOURS.map(() => 0));
        const counts = MONTHS.map(() => HOURS.map(() => 0));
        for (const cell of appData.cells) {
          if (
            cell.source !== state.source ||
            cell.location !== state.location ||
            cell.metric !== state.metric ||
            cell.year < Number(state.yearStart) ||
            cell.year > Number(state.yearEnd)
          ) continue;
          const month = Number(cell.month) - 1;
          const hour = Number(cell.hour);
          weighted[month][hour] += Number(cell.mean) * Number(cell.count);
          counts[month][hour] += Number(cell.count);
        }
        return MONTHS.map((_, month) => HOURS.map((_, hour) =>
          counts[month][hour] ? weighted[month][hour] / counts[month][hour] : null
        ));
      }

      function plotData(matrix) {
        const metric = selectedMetric();
        const hovertemplate = `Month %{y}<br>Hour %{x}:00<br>${metric.label} %{z:.2f} ${metric.unit}<extra></extra>`;
        const heatmap = {
          type: 'heatmap',
          x: HOURS,
          y: MONTHS,
          z: matrix,
          colorscale: COLORSCALE,
          colorbar: { title: { text: metric.unit } },
          hovertemplate,
          text: state.showValues ? matrix.map((row) => row.map((value) => value == null ? '' : value.toFixed(2))) : undefined,
          texttemplate: state.showValues ? '%{text}' : undefined,
          textfont: { size: Math.max(8, Number(state.tickFontSize) - 4), color: '#152033' }
        };
        const filledContour = {
          type: 'contour',
          x: HOURS,
          y: MONTHS,
          z: matrix,
          colorscale: COLORSCALE,
          colorbar: { title: { text: metric.unit } },
          contours: {
            coloring: 'heatmap',
            showlabels: Boolean(state.showContourLabels),
            showlines: true
          },
          line: { color: '#111827', width: state.preset === 'sae' ? 1.1 : 0.9 },
          showscale: true,
          hovertemplate
        };
        const lineContour = {
          type: 'contour',
          x: HOURS,
          y: MONTHS,
          z: matrix,
          contours: {
            coloring: 'none',
            showlabels: Boolean(state.showContourLabels),
            showlines: true
          },
          line: { color: '#111827', width: state.preset === 'sae' ? 1.1 : 0.9 },
          showscale: false,
          hovertemplate
        };
        if (state.plotType === 'heatmap') return [heatmap];
        if (state.plotType === 'contour') {
          return state.showValues ? [lineContour, valueTextTrace(matrix)] : [lineContour];
        }
        return state.showValues ? [filledContour, valueTextTrace(matrix)] : [filledContour];
      }

      function valueTextTrace(matrix) {
        const x = [];
        const y = [];
        const text = [];
        for (let month = 0; month < matrix.length; month += 1) {
          for (let hour = 0; hour < matrix[month].length; hour += 1) {
            const value = matrix[month][hour];
            if (value === null || value === undefined || Number.isNaN(value)) continue;
            x.push(hour);
            y.push(month + 1);
            text.push(value.toFixed(2));
          }
        }
        return {
          type: 'scatter',
          mode: 'text',
          x,
          y,
          text,
          textfont: { size: Math.max(8, Number(state.tickFontSize) - 4), color: '#152033' },
          hoverinfo: 'skip',
          showlegend: false
        };
      }

      function layout() {
        const metric = selectedMetric();
        return {
          width: Number(state.figureWidth),
          height: Number(state.figureHeight),
          title: {
            text: state.showTitle ? `<b>${state.figureTitle}</b>` : '',
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
            title: { text: 'Local hour [h]', font: { size: Number(state.axisTitleFontSize) } },
            tickmode: 'array',
            tickvals: HOURS,
            tickfont: { size: Number(state.tickFontSize) },
            gridcolor: state.preset === 'sae' ? '#d7dce3' : '#edf0f4',
            linecolor: '#000000',
            zeroline: false
          },
          yaxis: {
            title: { text: 'Month [-]', font: { size: Number(state.axisTitleFontSize) } },
            tickmode: 'array',
            tickvals: MONTHS,
            autorange: 'reversed',
            tickfont: { size: Number(state.tickFontSize) },
            gridcolor: state.preset === 'sae' ? '#d7dce3' : '#edf0f4',
            linecolor: '#000000',
            zeroline: false
          },
          margin: { l: 70, r: 55, t: state.showTitle ? 55 : 20, b: 112 },
          annotations: [{
            text: `${selectedLocation().name} · ${state.source} · ${metric.label} [${metric.unit}] · ${state.yearStart}-${state.yearEnd}`,
            xref: 'paper',
            yref: 'paper',
            x: 0,
            y: -0.44,
            showarrow: false,
            xanchor: 'left',
            font: { size: Math.max(10, Number(state.legendFontSize) - 2), color: '#4a5870' }
          }]
        };
      }

      function selectedMetric() {
        return appData.metrics.find((item) => item.id === state.metric) ?? { label: 'Value', unit: '' };
      }

      function selectedLocation() {
        return appData.locations.find((item) => item.id === state.location) ?? { name: '' };
      }
    </script>
  </body>
</html>
"""
