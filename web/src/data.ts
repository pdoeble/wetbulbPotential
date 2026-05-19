import initSqlJs, { Database } from 'sql.js';
import sqlWasmUrl from 'sql.js/dist/sql-wasm.wasm?url';
import type { AggregateRow, Manifest, MetricId } from './types';

const baseUrl = import.meta.env.BASE_URL;

export async function loadManifest(): Promise<Manifest> {
  const response = await fetch(`${baseUrl}data/manifest.json`);
  if (!response.ok) {
    throw new Error(`Could not load manifest: ${response.status}`);
  }
  return response.json() as Promise<Manifest>;
}

export async function loadDatabase(manifest: Manifest): Promise<Database> {
  const SQL = await initSqlJs({
    locateFile: () => sqlWasmUrl,
  });
  const response = await fetch(`${baseUrl}${manifest.database.path}`);
  if (!response.ok) {
    throw new Error(`Could not load processed database: ${response.status}`);
  }
  const bytes = new Uint8Array(await response.arrayBuffer());
  return new SQL.Database(bytes);
}

export function queryAggregates(
  db: Database,
  source: string,
  locationId: string,
  metric: MetricId,
  yearStart: number,
  yearEnd: number,
): AggregateRow[] {
  const statement = db.prepare(`
    SELECT source, location_id, metric, year, month, hour_local, count, mean, min, max
    FROM aggregates
    WHERE source = $source
      AND location_id = $location
      AND metric = $metric
      AND year BETWEEN $yearStart AND $yearEnd
    ORDER BY month, hour_local, year
  `);
  statement.bind({
    $source: source,
    $location: locationId,
    $metric: metric,
    $yearStart: yearStart,
    $yearEnd: yearEnd,
  });
  const rows: AggregateRow[] = [];
  while (statement.step()) {
    rows.push(statement.getAsObject() as unknown as AggregateRow);
  }
  statement.free();
  return rows;
}

export function buildMatrix(rows: AggregateRow[]): { z: (number | null)[][]; counts: number[][] } {
  const weightedSum = Array.from({ length: 12 }, () => Array.from({ length: 24 }, () => 0));
  const counts = Array.from({ length: 12 }, () => Array.from({ length: 24 }, () => 0));

  for (const row of rows) {
    const monthIndex = row.month - 1;
    const hourIndex = row.hour_local;
    if (monthIndex < 0 || monthIndex > 11 || hourIndex < 0 || hourIndex > 23) {
      continue;
    }
    weightedSum[monthIndex][hourIndex] += row.mean * row.count;
    counts[monthIndex][hourIndex] += row.count;
  }

  return {
    z: weightedSum.map((month, monthIndex) =>
      month.map((sum, hourIndex) =>
        counts[monthIndex][hourIndex] > 0 ? sum / counts[monthIndex][hourIndex] : null,
      ),
    ),
    counts,
  };
}
