# Datenquellen

## DWD

Quelle:

https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/moisture/

Der DWD-Importer unterstuetzt lokale `produkt_*.txt` Dateien und ZIP-Archive. Fuer Stuttgart wird
die vorhandene Datei `produkt_tf_stunde_20021101_20130514_04926.txt` als Referenz verwendet.

## NOAA Global Hourly

Quelle:

https://www.ncei.noaa.gov/data/global-hourly/access/

Dateimuster:

```text
https://www.ncei.noaa.gov/data/global-hourly/access/<JAHR>/<STATION_ID>.csv
```

Der Update-Workflow laedt NOAA jahresweise. Dadurch koennen bereits importierte Jahre uebersprungen
werden.

## NASA POWER

Quelle:

https://power.larc.nasa.gov/docs/services/api/temporal/hourly/

Der Update-Workflow laedt NASA POWER ebenfalls jahresweise pro Standort. `T2MWET` wird direkt als
Feuchtkugeltemperatur verwendet.

