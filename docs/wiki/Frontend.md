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

- `Analysis`
- `Percentiles`
- `Lines & Legend`
- `Figure & Export`

## Plottypen

- `Vehicles`: jede Datenreihe als Linie
- `Percentiles`: Perzentile ueber die ausgewaehlten Datenreihen
- `Interpolated color field`: Falschfarbenfeld zwischen Worst und Top

