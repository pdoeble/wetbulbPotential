# Update-Workflow

## Ziel

Der Online-Updatepfad soll trafficoptimiert sein:

- vorhandene RAW-DB pruefen
- vorhandene Download-Dateien wiederverwenden
- NOAA und NASA nur fuer fehlende Jahre nachladen
- danach die kleine Visualisierungsdatenbank neu exportieren

## Windows

Initialer Fill-run auf einer leeren Maschine oder fuer eine neu angelegte RAW-Datenbank:

```powershell
.\scripts\download_all_data.ps1 -DryRun
.\scripts\download_all_data.ps1
```

Inkrementelles Update:

```powershell
.\scripts\update_data.ps1 -DryRun
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

- `download_all_data.ps1` und `update_data.ps1` nutzen denselben inkrementellen Kern.
- Fuer neu ergaenzte Standorte reicht deshalb ein Update-Lauf; vorhandene Jahre werden uebersprungen.
- Der Fill-run ist semantisch fuer Erstbefuellung gedacht und ist bei vorhandener RAW-DB ebenfalls trafficoptimiert.
- DWD wird fuer bekannte historische Dateien nur einmal importiert.
- NOAA wird pro Standort und Jahr geprueft.
- NASA POWER wird pro Standort und Jahr geprueft.
- Der Export aktualisiert `web/public/data/wetbulb_processed.sqlite` und `manifest.json`.

## Statische Seite

```bash
python -m wetbulb_pipeline site --data web/public/data --out site
```

## Lokale Dash-GUI

```bash
python -m wetbulb_pipeline dash --data web/public/data
```
