from __future__ import annotations

import math


def saturation_vapor_pressure_hpa(temp_c: float) -> float:
    return 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))


def relative_humidity_from_dewpoint(temp_c: float, dewpoint_c: float) -> float:
    rh = 100.0 * saturation_vapor_pressure_hpa(dewpoint_c) / saturation_vapor_pressure_hpa(temp_c)
    return max(0.0, min(100.0, rh))


def wet_bulb_c(temp_c: float, dewpoint_c: float, pressure_hpa: float | None = None) -> float:
    """Return wet bulb temperature in C.

    Uses psychrolib when available. The fallback is Stull's approximation, which is
    adequate for ingestion QA and browser-facing climatological aggregates.
    """
    rh_pct = relative_humidity_from_dewpoint(temp_c, dewpoint_c)
    try:
        import psychrolib

        psychrolib.SetUnitSystem(psychrolib.SI)
        pressure_pa = (pressure_hpa or 1013.25) * 100.0
        return float(psychrolib.GetTWetBulbFromRelHum(temp_c, rh_pct / 100.0, pressure_pa))
    except Exception:
        rh = rh_pct
        return float(
            temp_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
            + math.atan(temp_c + rh)
            - math.atan(rh - 1.676331)
            + 0.00391838 * rh**1.5 * math.atan(0.023101 * rh)
            - 4.686035
        )


def station_pressure_from_sea_level_hpa(
    sea_level_hpa: float, elevation_m: float | None, temp_c: float | None = None
) -> float:
    if elevation_m is None:
        return sea_level_hpa
    temp_k = (temp_c if temp_c is not None else 15.0) + 273.15
    return sea_level_hpa * (1.0 - (0.0065 * elevation_m) / (temp_k + 0.0065 * elevation_m)) ** 5.257

