# Wetbulb Potential

Interaktive Auswertung der Feuchtkugelspreizung fuer ausgewaehlte Wetterstationen.

Die App zeigt, wie gross die Differenz zwischen Lufttemperatur und Feuchtkugeltemperatur ist:

```text
Delta T = T trocken - T feuchtkugel
```

Ein kleines Delta bedeutet feuchte, nahe gesaettigte Luft. Ein grosses Delta bedeutet trockenere Luft
und mehr moegliches Verdunstungskuehlpotenzial.

## App Nutzen

1. Standort waehlen.
2. Datenquelle waehlen.
3. Zeitraum und Metrik waehlen.
4. Darstellung waehlen:
   - Heatmap
   - Isolinien
   - Heatmap + Isolinien
5. Grafik ueber die Plotly-Menueleiste als Bild exportieren.

Die Standardansicht ist eine 12 x 24 Darstellung:

- Zeilen: Monate 1 bis 12
- Spalten: lokale Uhrzeit 0 bis 23
- Farbwert: Mittelwert der gewaehlten Metrik

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

