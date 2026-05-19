import { useEffect, useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import type { Data, Layout } from 'plotly.js';
import { buildMatrix, loadDatabase, loadManifest, queryAggregates } from './data';
import type { Manifest, Metric, MetricId, PlotPreset, PlotType } from './types';

const HOURS = Array.from({ length: 24 }, (_, index) => index);
const MONTHS = Array.from({ length: 12 }, (_, index) => index + 1);
const DEFAULT_METRIC: MetricId = 'delta_t_k';

function App() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [db, setDb] = useState<Awaited<ReturnType<typeof loadDatabase>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState('');
  const [locationId, setLocationId] = useState('');
  const [metric, setMetric] = useState<MetricId>(DEFAULT_METRIC);
  const [yearStart, setYearStart] = useState(2002);
  const [yearEnd, setYearEnd] = useState(2013);
  const [plotType, setPlotType] = useState<PlotType>('heatmap');
  const [preset, setPreset] = useState<PlotPreset>('sae');
  const [showValues, setShowValues] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const nextManifest = await loadManifest();
        if (cancelled) return;
        setManifest(nextManifest);
        const firstAvailability = nextManifest.availability[0];
        if (firstAvailability) {
          setSource(firstAvailability.source);
          setLocationId(firstAvailability.location_id);
          setMetric(firstAvailability.metric);
          setYearStart(firstAvailability.year_min);
          setYearEnd(firstAvailability.year_max);
        }
        const nextDb = await loadDatabase(nextManifest);
        if (!cancelled) setDb(nextDb);
      } catch (cause) {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const availableSources = useMemo(() => {
    if (!manifest) return [];
    return Array.from(new Set(manifest.availability.map((item) => item.source))).sort();
  }, [manifest]);

  const availableLocations = useMemo(() => {
    if (!manifest || !source) return [];
    const ids = new Set(
      manifest.availability.filter((item) => item.source === source).map((item) => item.location_id),
    );
    return manifest.locations.filter((location) => ids.has(location.id));
  }, [manifest, source]);

  const availableMetrics = useMemo(() => {
    if (!manifest || !source || !locationId) return [];
    const ids = new Set(
      manifest.availability
        .filter((item) => item.source === source && item.location_id === locationId)
        .map((item) => item.metric),
    );
    return manifest.metrics.filter((item) => ids.has(item.id));
  }, [manifest, source, locationId]);

  const selectedAvailability = useMemo(() => {
    return manifest?.availability.find(
      (item) =>
        item.source === source && item.location_id === locationId && item.metric === metric,
    );
  }, [manifest, source, locationId, metric]);

  useEffect(() => {
    if (!availableLocations.some((location) => location.id === locationId)) {
      setLocationId(availableLocations[0]?.id ?? '');
    }
  }, [availableLocations, locationId]);

  useEffect(() => {
    if (!availableMetrics.some((item) => item.id === metric)) {
      setMetric(availableMetrics[0]?.id ?? DEFAULT_METRIC);
    }
  }, [availableMetrics, metric]);

  useEffect(() => {
    if (selectedAvailability) {
      setYearStart(selectedAvailability.year_min);
      setYearEnd(selectedAvailability.year_max);
    }
  }, [selectedAvailability?.year_min, selectedAvailability?.year_max]);

  const selectedMetric: Metric | undefined = manifest?.metrics.find((item) => item.id === metric);
  const selectedLocation = manifest?.locations.find((location) => location.id === locationId);

  const rows = useMemo(() => {
    if (!db || !source || !locationId || !metric) return [];
    return queryAggregates(db, source, locationId, metric, yearStart, yearEnd);
  }, [db, source, locationId, metric, yearStart, yearEnd]);

  const matrix = useMemo(() => buildMatrix(rows), [rows]);
  const plotData = useMemo(
    () => buildPlotData(matrix.z, plotType, selectedMetric, showValues),
    [matrix.z, plotType, selectedMetric, showValues],
  );
  const layout = useMemo(
    () => buildLayout(selectedLocation?.name ?? '', selectedMetric, yearStart, yearEnd, preset),
    [selectedLocation?.name, selectedMetric, yearStart, yearEnd, preset],
  );

  if (error) {
    return <main className="app app-message">Fehler beim Laden: {error}</main>;
  }

  if (!manifest || !db) {
    return <main className="app app-message">Daten werden geladen...</main>;
  }

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <h1>Wetbulb Potential</h1>
          <p>Station climatology for dry-bulb to wet-bulb spread.</p>
        </div>
        <div className="status">
          <span>{formatBytes(manifest.database.size_bytes)}</span>
          <span>{rows.reduce((sum, row) => sum + row.count, 0).toLocaleString()} obs</span>
        </div>
      </header>

      <section className="controls" aria-label="Plot controls">
        <label>
          Quelle
          <select value={source} onChange={(event) => setSource(event.target.value)}>
            {availableSources.map((item) => (
              <option key={item} value={item}>
                {sourceLabel(manifest, item)}
              </option>
            ))}
          </select>
        </label>

        <label>
          Standort
          <select value={locationId} onChange={(event) => setLocationId(event.target.value)}>
            {availableLocations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Metrik
          <select value={metric} onChange={(event) => setMetric(event.target.value as MetricId)}>
            {availableMetrics.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Von
          <select
            value={yearStart}
            onChange={(event) => setYearStart(Number(event.target.value))}
          >
            {yearOptions(selectedAvailability).map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>

        <label>
          Bis
          <select value={yearEnd} onChange={(event) => setYearEnd(Number(event.target.value))}>
            {yearOptions(selectedAvailability).map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>

        <label>
          Darstellung
          <select value={plotType} onChange={(event) => setPlotType(event.target.value as PlotType)}>
            {manifest.plot_types.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Preset
          <select value={preset} onChange={(event) => setPreset(event.target.value as PlotPreset)}>
            <option value="sae">SAE Paper</option>
            <option value="excel">Excel Reference</option>
          </select>
        </label>

        <label className="checkbox-control">
          <input
            type="checkbox"
            checked={showValues}
            onChange={(event) => setShowValues(event.target.checked)}
          />
          Werte
        </label>
      </section>

      <section className="plot-shell" aria-label="Wetbulb plot">
        <Plot
          data={plotData}
          layout={layout}
          config={{
            responsive: true,
            displaylogo: false,
            toImageButtonOptions: {
              format: 'png',
              filename: `${locationId}_${metric}_${yearStart}_${yearEnd}`,
              scale: 3,
            },
          }}
          useResizeHandler
          className="plot"
        />
      </section>

      <footer className="footnote">
        {selectedLocation?.name} · {selectedLocation?.timezone} · {sourceLabel(manifest, source)}
      </footer>
    </main>
  );
}

function buildPlotData(
  z: (number | null)[][],
  plotType: PlotType,
  metric?: Metric,
  showValues = false,
): Data[] {
  const colorscale: [number, string][] = [
    [0, '#2451a6'],
    [0.25, '#2aa7a2'],
    [0.5, '#f1d46b'],
    [0.75, '#ec8f3c'],
    [1, '#a83232'],
  ];
  const hovertemplate = `Month %{y}<br>Hour %{x}:00<br>${metric?.label ?? 'Value'} %{z:.2f} ${
    metric?.unit ?? ''
  }<extra></extra>`;
  const heatmap: Data = {
    type: 'heatmap',
    x: HOURS,
    y: MONTHS,
    z,
    colorscale,
    colorbar: { title: { text: metric?.unit ?? '' } },
    hovertemplate,
    text: (showValues
      ? z.map((row) => row.map((value) => (value == null ? '' : value.toFixed(2))))
      : undefined) as unknown as string[] | undefined,
    texttemplate: showValues ? '%{text}' : undefined,
    textfont: { size: 10, color: '#152033' },
  };
  const contour: Data = {
    type: 'contour',
    x: HOURS,
    y: MONTHS,
    z,
    contours: { coloring: plotType === 'contour' ? 'heatmap' : 'lines', showlabels: true },
    line: { color: '#1a1f29', width: 1 },
    colorscale,
    showscale: plotType === 'contour',
    colorbar: { title: { text: metric?.unit ?? '' } },
    hovertemplate,
  };
  if (plotType === 'heatmap') return [heatmap];
  if (plotType === 'contour') return [contour];
  return [heatmap, contour];
}

function buildLayout(
  locationName: string,
  metric: Metric | undefined,
  yearStart: number,
  yearEnd: number,
  preset: PlotPreset,
): Partial<Layout> {
  const isSae = preset === 'sae';
  return {
    title: {
      text: `${metric?.label ?? 'Metric'} · ${locationName} · ${yearStart}-${yearEnd}`,
      x: 0.02,
      xanchor: 'left',
      font: { size: isSae ? 18 : 16, color: '#152033' },
    },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    margin: { l: 70, r: 40, t: 64, b: 70 },
    xaxis: {
      title: { text: 'Local hour' },
      tickmode: 'array',
      tickvals: HOURS,
      gridcolor: isSae ? '#d7dce3' : '#edf0f4',
      zeroline: false,
    },
    yaxis: {
      title: { text: 'Month' },
      tickmode: 'array',
      tickvals: MONTHS,
      autorange: 'reversed',
      gridcolor: isSae ? '#d7dce3' : '#edf0f4',
      zeroline: false,
    },
    font: { family: 'Arial, sans-serif', size: isSae ? 13 : 12, color: '#152033' },
  };
}

function yearOptions(availability?: { year_min: number; year_max: number }): number[] {
  if (!availability) return [];
  return Array.from(
    { length: availability.year_max - availability.year_min + 1 },
    (_, index) => availability.year_min + index,
  );
}

function sourceLabel(manifest: Manifest, id: string): string {
  return manifest.sources.find((source) => source.id === id)?.label ?? id;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default App;
