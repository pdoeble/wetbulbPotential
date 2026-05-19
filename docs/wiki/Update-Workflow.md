# Update-Workflow

## Ziel

Der Online-Updatepfad soll trafficoptimiert sein:

- vorhandene RAW-DB pruefen
- vorhandene Download-Dateien wiederverwenden
- NOAA und NASA nur fuer fehlende Jahre nachladen
- danach die kleine Visualisierungsdatenbank neu exportieren

## Windows

Dry-run:

```powershell
.\scripts\update_data.ps1 -DryRun
```

Echtes Update:

```powershell
.\scripts\update_data.ps1
```

## Bash

```bash
./scripts/update_data.sh
```

## Direkte CLI

```bash
python -m wetbulb_pipeline update --years 2002 2013 --sources dwd noaa nasa
```

Nur bestimmte Quellen:

```bash
python -m wetbulb_pipeline update --sources noaa nasa
```

## Verhalten

- DWD wird fuer bekannte historische Dateien nur einmal importiert.
- NOAA wird pro Standort und Jahr geprueft.
- NASA POWER wird pro Standort und Jahr geprueft.
- Der Export aktualisiert `web/public/data/wetbulb_processed.sqlite` und `manifest.json`.

