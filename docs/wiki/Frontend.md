# Frontend

## Stack

- Dash fuer die lokale GUI
- Plotly fuer die Grafik
- statisches HTML/JavaScript fuer GitHub Pages

## Datenladen

Die statische Seite laedt:

```text
assets/data.json
```

Diese Datei wird durch den Python-Site-Build aus `web/public/data/wetbulb_processed.sqlite`
erzeugt.

## Settings

Die Settings sind identisch fuer Dash und statische Seite:

- `Data`
- `Plot`
- `Figure & Export`

Die Panels stehen auf breiten Viewports als Spalten nebeneinander.

## Plottypen

- `Heatmap`: 12 x 24 Colorplot
- `Isolines`: 12 x 24 Isoliniendarstellung
- `Heatmap + isolines`: Colorplot mit ueberlagerten Isolinien, Default
