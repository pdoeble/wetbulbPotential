# Architektur

## Ziel

Das Projekt trennt lokale Rohdatenverarbeitung und statische GitHub-Pages-Visualisierung.

## Komponenten

- `wetbulb_pipeline/`: Python-Paket fuer Import, Normalisierung, SQLite-Speicherung und Export.
- `configs/stations.yml`: Standortkatalog mit DWD-, NOAA- und NASA-Zuordnung.
- `data/raw/`: gitignored; enthaelt Downloads und `wetbulb_raw.sqlite`.
- `web/public/data/`: versionierbare Visualisierungsdaten unter 100 MB.
- `web/`: Vite React TypeScript App mit Plotly und `sql.js`.

## Datenfluss

1. Importer lesen DWD, NOAA oder NASA.
2. Messwerte werden in ein gemeinsames Beobachtungsschema normalisiert.
3. RAW-Daten landen lokal in `data/raw/wetbulb_raw.sqlite`.
4. Der Export erzeugt aggregierte Daten in `web/public/data/wetbulb_processed.sqlite`.
5. Die App liest `manifest.json` und fragt die prozessierte SQLite-Datei im Browser ab.

## Groessengrenze

Die prozessierte Datenbank darf maximal 100 MB gross sein. Die RAW-Datenbank ist nicht versioniert.

