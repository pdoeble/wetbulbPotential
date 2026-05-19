# Tests

## Python

```bash
pytest
ruff check .
```

Abgedeckt:

- DWD-Golden-Werte Stuttgart
- DWD/NOAA/NASA Parser
- idempotenter Import
- Export von Manifest und prozessierter SQLite-Datei
- 12 x 24 Matrixbildung fuer die Visualisierung
- Site-Schema mit `index.html`, `assets/data.json`, `.nojekyll`
- Standard-Controls und Default-Werte

## Static Site

```bash
python -m wetbulb_pipeline site --data web/public/data --out site
```

Der Build erzeugt die statische GitHub-Pages-App.

## Browser-Smoke-Test

```bash
python -m http.server 8060 --directory site
```

Dann per Browser oder Playwright pruefen:

- Plot rendert
- Default-Settings stimmen
- Settings-Panels existieren
- SVG-Export ist erreichbar
