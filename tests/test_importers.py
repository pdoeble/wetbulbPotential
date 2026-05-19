from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError

from wetbulb_pipeline.config import get_location
from wetbulb_pipeline.importers import noaa
from wetbulb_pipeline.importers.nasa import read_observations as read_nasa
from wetbulb_pipeline.importers.noaa import read_observations as read_noaa


def test_noaa_parser_decodes_scaled_fields_and_missing_values(tmp_path: Path) -> None:
    sample = tmp_path / "noaa.csv"
    header = (
        '"STATION","DATE","LATITUDE","LONGITUDE","ELEVATION","NAME","REPORT_TYPE",'
        '"QUALITY_CONTROL","WND","TMP","DEW","SLP"'
    )
    good_row = (
        '"72278023183","2024-01-01T00:00:00","33.4278","-112.00365","339.2",'
        '"PHOENIX AIRPORT, AZ US","FM-12","V020","999,9,C,0000,1",'
        '"+0172,1","+0039,1","10188,1"'
    )
    missing_row = (
        '"72278023183","2024-01-01T01:00:00","33.4278","-112.00365","339.2",'
        '"PHOENIX AIRPORT, AZ US","FM-12","V020","999,9,C,0000,1",'
        '"+9999,1","+0039,1","10188,1"'
    )
    sample.write_text(
        "\n".join([header, good_row, missing_row]),
        encoding="utf-8",
    )
    location = get_location("phoenix-sky-harbor")

    observations = read_noaa(sample, location)

    assert len(observations) == 2
    assert observations[0].dry_bulb_c == 17.2
    assert observations[0].dew_point_c == 3.9
    assert observations[0].wet_bulb_c is not None
    assert observations[0].valid is True
    assert observations[1].dry_bulb_c is None
    assert observations[1].valid is False


def test_nasa_parser_skips_header_and_handles_missing_values(tmp_path: Path) -> None:
    sample = tmp_path / "nasa.csv"
    sample.write_text(
        "\n".join(
            [
                "-BEGIN HEADER-",
                "NASA/POWER Source Native Resolution Hourly Data",
                "-END HEADER-",
                "YEAR,MO,DY,HR,T2M,T2MWET,T2MDEW,RH2M,PS,WS10M,ALLSKY_SFC_SW_DWN",
                "2024,1,1,0,7.38,4.65,1.92,68.16,96.11,2.71,153.4",
                "2024,1,1,1,-999,4.34,1.60,68.04,96.09,2.88,-999",
            ]
        ),
        encoding="utf-8",
    )
    location = get_location("phoenix-sky-harbor")

    observations = read_nasa(sample, location, time_standard="UTC")

    assert len(observations) == 2
    assert observations[0].source == "NASA_POWER"
    assert observations[0].pressure_hpa == 961.1
    assert observations[0].solar_radiation_w_m2 == 153.4
    assert observations[0].valid is True
    assert observations[1].dry_bulb_c is None
    assert observations[1].solar_radiation_w_m2 is None
    assert observations[1].valid is False


def test_noaa_download_404_writes_missing_marker(tmp_path, monkeypatch) -> None:
    def fail_404(url: str, target: Path) -> None:
        raise HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr(noaa, "urlretrieve", fail_404)

    downloaded = noaa.download_year("00000099999", 2002, tmp_path)

    assert downloaded is None
    marker = tmp_path / "00000099999_2002.missing"
    assert marker.exists()
    assert "404 Not Found" in marker.read_text(encoding="utf-8")
