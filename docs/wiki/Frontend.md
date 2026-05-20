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
- `Map`
- `Figure & Export`

Die Panels stehen auf breiten Viewports als Spalten nebeneinander.

## Plottypen

- `Heatmap`: 12 x 24 Colorplot
- `Isolines`: 12 x 24 Isoliniendarstellung
- `Heatmap + isolines`: Colorplot mit ueberlagerten Isolinien, Default

## Plot-Optionen

- `Color fill`: `Interpolated` fuer geglaettete Plotly-Contour-Farbfuellung oder `Grid cells`
  fuer die sichtbare 12 x 24 Rasterdarstellung.
- Isolinien werden ueber erste Linie und Schrittweite definiert. Default ist `0 K` in
  `1 K`-Schritten.
- `cmin` und `cmax` fixieren nur die Farbskala, nicht die Isolinien.
- Monats-Ticks werden als `Jan` bis `Dec` angezeigt. Stunden-Ticks stehen alle zwei Stunden
  waagerecht.

## Karte

Die Karte steht links vom Plot. Der aktuelle Kartenausschnitt wird als
`[lon_min,lon_max,lat_min,lat_max]` im Setting `Map viewport` gespeichert, bei interaktivem Zoomen
aktualisiert und beim SVG-Export der Karte verwendet. Presets gibt es fuer World, Europe, North
America, Middle East und Asia (India to Japan).
