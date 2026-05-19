# Frontend

## Stack

- Vite
- React
- TypeScript
- Plotly
- sql.js

## Datenladen

Die App laedt zuerst:

```text
data/manifest.json
```

Danach laedt sie:

```text
data/wetbulb_processed.sqlite
```

`sql.js` wird mit einer von Vite erzeugten WASM-Asset-URL initialisiert. Dadurch funktioniert der
WASM-Pfad lokal und auf GitHub Pages ohne manuell kopierte Public-Datei.

## Plottypen

- Heatmap
- Isolinien
- Heatmap + Isolinien

Die Matrix ist immer Monat x lokale Stunde.

