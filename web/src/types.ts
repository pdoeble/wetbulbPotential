export type MetricId =
  | 'delta_t_k'
  | 'dry_bulb_c'
  | 'wet_bulb_c'
  | 'relative_humidity_pct'
  | 'pressure_hpa';

export type PlotType = 'heatmap' | 'contour' | 'combined';
export type PlotPreset = 'excel' | 'sae';

export interface ManifestLocation {
  id: string;
  name: string;
  country: string;
  climate_label: string;
  latitude: number;
  longitude: number;
  elevation_m: number | null;
  timezone: string;
  dwd_station_id: string | null;
  noaa_station_id: string | null;
  nasa_enabled: number;
}

export interface Availability {
  source: string;
  location_id: string;
  metric: MetricId;
  year_min: number;
  year_max: number;
  cells: number;
}

export interface Metric {
  id: MetricId;
  label: string;
  unit: string;
}

export interface Manifest {
  version: number;
  database: {
    path: string;
    size_bytes: number;
  };
  locations: ManifestLocation[];
  availability: Availability[];
  metrics: Metric[];
  plot_types: Array<{ id: PlotType; label: string }>;
  sources: Array<{ id: string; label: string; url: string; license: string }>;
}

export interface AggregateRow {
  source: string;
  location_id: string;
  metric: MetricId;
  year: number;
  month: number;
  hour_local: number;
  count: number;
  mean: number;
  min: number;
  max: number;
}

