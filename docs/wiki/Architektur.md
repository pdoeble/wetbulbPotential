# Architektur

## Ziel

Das Projekt trennt lokale Rohdatenverarbeitung und statische GitHub-Pages-Visualisierung.

## Komponenten

- `wetbulb_pipeline/`: Python-Paket fuer Import, Normalisierung, SQLite-Speicherung und Export.
- `configs/stations.yml`: Standortkatalog mit DWD-, NOAA- und NASA-Zuordnung.
- `data/raw/`: gitignored; enthaelt Downloads und `wetbulb_raw.sqlite`.
- `web/public/data/`: versionierbare Visualisierungsdaten unter 100 MB.
- `wetbulb_pipeline/dash_app.py`: lokale Dash-/Plotly-GUI.
- `wetbulb_pipeline/site.py`: statischer GitHub-Pages-Build.

## Datenfluss

1. Importer lesen DWD, NOAA oder NASA.
2. Messwerte werden in ein gemeinsames Beobachtungsschema normalisiert.
3. RAW-Daten landen lokal in `data/raw/wetbulb_raw.sqlite`.
4. Der Export erzeugt aggregierte Daten in `web/public/data/wetbulb_processed.sqlite`.
5. `site` wandelt die prozessierte SQLite-Datei in `site/assets/data.json` um.
6. Dash und die statische Seite nutzen dieselbe Settings-/Datenstruktur.

## Groessengrenze

Die prozessierte Datenbank darf maximal 100 MB gross sein. Die RAW-Datenbank ist nicht versioniert.
