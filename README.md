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
4. Darstellung waehlen:
   - `Heatmap`
   - `Isolines`
   - `Heatmap + isolines`
5. Farbfuellung, Isolinien, Farbskala, Kartenausschnitt und Schriftgroessen einstellen.
6. Grafik und aktuelle Kartenansicht als SVG exportieren.

## Einstellungen

Die Einstellungen sind in vier Gruppen organisiert:

- `Data`
- `Plot`
- `Map`
- `Figure & Export`

Wichtige Defaults:

- Display: `Heatmap + isolines`
- Color fill: `Interpolated`
- Isolines: erste Linie `0 K`, Schrittweite `1 K`
- Color scale: `cmin = 0`, `cmax = 16`
- Jahre: automatisch voller verfuegbarer Zeitraum der gewaehlten Quelle/Location/Metrik
- Map preset: `World`; weitere Presets sind `Europe`, `North America`, `Middle East` und
  `Asia (India to Japan)`
- X axis: `Local hour [h]`
- Y axis: `Month [-]`
- Font family: `Times New Roman`
- Figure size: `500 x 400 px`

## Datenansicht

Die Daten werden als 12 x 24 Matrix ausgewertet:

- X-Achse: lokale Uhrzeit 0 bis 23
- X-Achsenbeschriftung: jede zweite Stunde, waagerecht
- Y-Achse: englische Monatsnamen `Jan` bis `Dec`
- Zellwerte: gewichteter Mittelwert ueber den ausgewaehlten Jahresbereich
- Darstellungsformen: interpolierte Farbfuellung oder Rasterzellen, Isolinien oder Farbfuellung
  mit Isolinien
- `cmin` und `cmax` fixieren nur die Farbskala. Die Isolinien werden separat ueber erste Linie
  und Schrittweite definiert.
- Der Plottitel enthaelt Standort und Land in der ersten Zeile und `Wetbulb Potential` in der
  zweiten Zeile.
- Die Fusszeile unter dem Plot zeigt nur Quelle und Zeitraum, z. B.
  `Data Source: NASA_POWER 2002-2025`.

## Karte Und Export

Die Standortkarte steht links neben dem Plot. Die Settings liegen darunter. Der aktuelle Zoom wird
im Textfeld `Map viewport [lon_min,lon_max,lat_min,lat_max]` gehalten und bei interaktivem Zoomen
aktualisiert. Der Wert kann kopiert, spaeter wieder eingefuegt und ueber Presets gesetzt werden.

Der Karten-SVG-Export verwendet die aktuelle Zoom-/Viewport-Einstellung. Der Plot-SVG-Export nutzt
die eingestellte Figure-Groesse.

## Metriken

Der versionierte GitHub-Pages-Datensatz exportiert standardmaessig `Delta T dry bulb - wet bulb`,
damit die Visualisierungsdatenbank unter dem GitHub-Limit von 100 MB bleibt. Die Pipeline kann fuer
lokale Analysen weiterhin alle Metriken exportieren.

| Metrik | Bedeutung | Einheit |
| --- | --- | --- |
| Delta T dry bulb - wet bulb | Lufttemperatur minus Feuchtkugeltemperatur | K |
| Dry bulb temperature | Lufttemperatur | degC |
| Wet bulb temperature | Feuchtkugeltemperatur | degC |
| Relative humidity | Relative Feuchte | % |
| Pressure | Luftdruck | hPa |
| Solar radiation | Kurzwellige Einstrahlung aus NASA POWER | W/m2 |

## Standortkatalog

Der Katalog enthaelt DWD/NOAA-Stationsstandorte und zusaetzliche Track-/Road-Testorte fuer
PKW-Kuehlsystemauslegung. Fuer die Track-/Road-Orte ist NASA POWER die primaere Quelle, damit fuer
jeden Punkt sofort eine 12 x 24 Auswertung nach Monat und lokaler Uhrzeit erzeugt werden kann.

Neu enthalten sind u. a.:

- Affalterbach, Immendingen, Nuerburgring, Hockenheim, Bilster Berg, Sachsenring, Gross Doelln,
  Leipheim und Lueneburg
- Napa Valley, Sonoma Raceway, Circuit of The Americas und Road Atlanta
- Monza, Barberino Tavarnelle, Sibenik, Spa-Francorchamps, St Nikolai im Sausal
- Sorsele und Arjeplog fuer Winter-/Kaltklima

`Saalfelden_unconfirmed` ist bewusst als ungeklaert markiert, weil der Ausgangsort als
`Saalfelder Österreich` notiert war.

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
- `ALLSKY_SFC_SW_DWN`: kurzwellige Solarstrahlung

NASA POWER ist kein lokales Stationsmessnetz, sondern ein globales Punkt-/Rasterprodukt. Es ist
nuetzlich als Fallback, wenn fuer einen Standort keine passende Stationsreihe verfuegbar ist.

## Daten Laden Und Aktualisieren

Vor jedem echten Lauf empfiehlt sich ein Dry-run. Er zeigt, welche Dateien fehlen und welche Jahre
bereits in der lokalen RAW-Datenbank vorhanden sind.

Initialer Fill-run fuer alle konfigurierten Quellen und Standorte:

```powershell
.\scripts\download_all_data.ps1 -DryRun
.\scripts\download_all_data.ps1
```

Inkrementelles Update:

```powershell
.\scripts\update_data.ps1 -DryRun
.\scripts\update_data.ps1
```

Fuer neu hinzugefuegte Standorte reicht normalerweise das inkrementelle Update. Die Pipeline prueft
pro Quelle, Standort und Jahr, was schon vorhanden ist, und laedt nur fehlende Jahresdateien nach.
Der Fill-run ist die passende Wahl fuer eine leere Maschine oder eine neu angelegte RAW-Datenbank.
Falls NOAA fuer eine Station/Jahr-Kombination kein CSV bereitstellt, wird dies als `.missing`
vermerkt und der Lauf setzt mit den naechsten Daten fort.

Der Standardexport fuer Pages ist bewusst klein:

```bash
python -m wetbulb_pipeline export
```

Falls ein lokaler Dash-Server oder ein SQLite-Viewer die veroeffentlichte Datenbank sperrt, fragt
das Update interaktiv, ob die lokalen Prozesse beendet werden sollen. Nach erfolgreichem Export kann
der Server auf Wunsch direkt neu gestartet werden.

Ein lokaler Voll-Export mit allen Metriken ist moeglich, aber nicht fuer den Commit nach GitHub
Pages gedacht:

```bash
python -m wetbulb_pipeline export --metrics all --max-mb 250
```

## Hinweise Zur Interpretation

- DWD und NOAA sind Stationsdaten. NASA POWER ist ein globales Raster-/Reanalyseprodukt.
- Alle 12 x 24 Grafiken sind Mittelwerte ueber viele Wetterlagen. Extremfaelle werden dadurch
  geglaettet.
- Die Uhrzeit ist in der App als lokale Stationszeit dargestellt.
- Fuer technische Grenzfallanalysen sollten neben Mittelwerten auch Min/Max-Werte und
  konkrete Einzelstunden betrachtet werden.

## Lokal Oeffnen

```bash
python -m wetbulb_pipeline dash --data web/public/data
```

Danach im Browser oeffnen:

```text
http://127.0.0.1:8050/
```
