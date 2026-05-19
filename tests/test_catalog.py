from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from wetbulb_pipeline.config import load_locations

NEW_SITE_IDS = {
    "DE_AFFALTERBACH_ROAD",
    "DE_IMMENDINGEN_TRACK",
    "DE_NUERBURGRING_TRACK",
    "DE_HOCKENHEIM_TRACK",
    "US_NAPA_ROAD",
    "US_SONOMA_TRACK",
    "IT_BARBERINO_ROAD",
    "US_COTA_TRACK",
    "US_ROAD_ATLANTA_TRACK",
    "HR_SIBENIK_ROAD",
    "AT_ST_NIKOLAI_ROAD",
    "SE_SORSELE_TRACK",
    "DE_LUENEBURG_TRACK",
    "DE_BILSTER_BERG_TRACK",
    "DE_GROSS_DOELLN_TRACK",
    "DE_SACHSENRING_TRACK",
    "DE_LEIPHEIM_TRACK",
    "AT_SAALFELDEN_TRACK",
    "SE_ARJEPLOG_TRACK",
    "BE_SPA_TRACK",
    "IT_MONZA_TRACK",
}


def test_track_and_road_catalog_locations_are_configured() -> None:
    locations = {location.site_id: location for location in load_locations()}
    assert NEW_SITE_IDS <= set(locations)

    for site_id in NEW_SITE_IDS:
        location = locations[site_id]
        assert location.site_type in {"Road", "Track"}
        assert location.priority in {1, 2, 3}
        assert location.climate_tags
        assert location.primary_source == "NASA_POWER_HOURLY_POINT"
        assert location.primary_access_url is not None

        parsed = urlparse(location.primary_access_url)
        query = parse_qs(parsed.query)
        parameters = query["parameters"][0].split(",")
        assert parsed.netloc == "power.larc.nasa.gov"
        assert query["start"] == ["20020101"]
        assert query["end"] == ["20131231"]
        assert "T2M" in parameters
        assert "T2MWET" in parameters
        assert "PS" in parameters
        assert "RH2M" in parameters
        assert "ALLSKY_SFC_SW_DWN" in parameters


def test_saalfelden_remains_marked_as_unresolved() -> None:
    locations = {location.site_id: location for location in load_locations()}
    saalfelden = locations["AT_SAALFELDEN_TRACK"]
    assert "unresolved" in saalfelden.climate_tags
    assert saalfelden.notes is not None
    assert "Saalfelder" in saalfelden.notes
