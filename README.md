# Wetbulb Potential

Interaktive Auswertung der Feuchtkugelspreizung fuer ausgewaehlte Wetterstationen.

Die App zeigt, wie gross die Differenz zwischen Lufttemperatur und Feuchtkugeltemperatur ist:

```text
Delta T = T trocken - T feuchtkugel
```

Ein kleines Delta bedeutet feuchte, nahe gesaettigte Luft. Ein grosses Delta bedeutet trockenere Luft
und mehr moegliches Verdunstungskuehlpotenzial.

## App Nutzen

Die Analyseansicht ist die erste Ansicht. Es gibt keine Landingpage.

1. Standort waehlen.
2. Datenquelle waehlen.
3. Zeitraum und Metrik waehlen.
4. Plot-Modus waehlen:
   - `Vehicles`: einzelne Monats-/Jahresdatenreihen
   - `Percentiles`: Perzentilkurven ueber die ausgewaehlten Datenreihen
5. Darstellung waehlen:
   - `Lines`
   - `Interpolated color field`
6. Grafik als SVG exportieren.

## Einstellungen

Die Einstellungen sind in vier Gruppen organisiert:

- `Analysis`
- `Percentiles`
- `Lines & Legend`
- `Figure & Export`

Wichtige Defaults:

- Plot mode: `Percentiles`
- X axis: `Local hour [h]`
- Y axis: `Relative wetbulb spread [%]`
- Font family: `Times New Roman`
- Figure size: `500 x 400 px`
- Marker size: `0`

## Datenansicht

Die Daten werden als Stundenkurven ausgewertet:

- X-Achse: lokale Uhrzeit 0 bis 23
- Datenreihen: Monats-/Jahreskurven der ausgewaehlten Quelle, Station und Metrik
- Perzentile: aus den ausgewaehlten Kurven interpoliert und berechnet

## Metriken

| Metrik | Bedeutung | Einheit |
| --- | --- | --- |
| Delta T dry bulb - wet bulb | Lufttemperatur minus Feuchtkugeltemperatur | K |
| Dry bulb temperature | Lufttemperatur | degC |
| Wet bulb temperature | Feuchtkugeltemperatur | degC |
| Relative humidity | Relative Feuchte | % |
| Pressure | Luftdruck | hPa |

## Datenquellen

### Deutscher Wetterdienst

DWD Climate Data Center, stundenweise Feuchteparameter:

https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/moisture/

Enthaltene DWD-Parameter fuer diese Auswertung:

- `TT_STD`: Lufttemperatur in 2 m Hoehe
- `TF_STD`: Feuchttemperatur / Feuchtkugeltemperatur
- `RF_STD`: relative Feuchte
- `TD_STD`: Taupunkttemperatur
- `P_STD`: Luftdruck

Lizenz: Creative Commons BY 4.0.

### NOAA NCEI Global Hourly / ISD

Weltweite Stationsdaten:

https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database

Direkter CSV-Zugriff:

https://www.ncei.noaa.gov/data/global-hourly/access/

Genutzte NOAA-Felder:

- `DATE`: Zeitstempel
- `TMP`: Lufttemperatur
- `DEW`: Taupunkt
- `SLP`: Seespiegeldruck
- `WND`: Wind
- `QUALITY_CONTROL` und Feldflags: Qualitaetshinweise

Bei NOAA wird die Feuchtkugeltemperatur aus Temperatur, Taupunkt und Druck berechnet.

### NASA POWER

Globales stundenweises Rasterprodukt:

https://power.larc.nasa.gov/docs/services/api/temporal/hourly/

Genutzte NASA-Parameter:

- `T2M`: Lufttemperatur in 2 m
- `T2MWET`: Feuchtkugeltemperatur in 2 m
- `T2MDEW`: Taupunkt
- `RH2M`: relative Feuchte
- `PS`: Oberflaechendruck
- `WS10M`: Windgeschwindigkeit

NASA POWER ist kein lokales Stationsmessnetz, sondern ein globales Punkt-/Rasterprodukt. Es ist
nuetzlich als Fallback, wenn fuer einen Standort keine passende Stationsreihe verfuegbar ist.

## Hinweise Zur Interpretation

- DWD und NOAA sind Stationsdaten. NASA POWER ist ein globales Raster-/Reanalyseprodukt.
- Alle 12 x 24 Grafiken sind Mittelwerte ueber viele Wetterlagen. Extremfaelle werden dadurch
  geglaettet.
- Die Uhrzeit ist in der App als lokale Stationszeit dargestellt.
- Fuer technische Grenzfallanalysen sollten neben Mittelwerten auch Min/Max, Perzentile und
  konkrete Einzelstunden betrachtet werden.

## Lokal Oeffnen

```bash
python -m wetbulb_pipeline dash --data web/public/data
```

Danach im Browser oeffnen:

```text
http://127.0.0.1:8050/
```
