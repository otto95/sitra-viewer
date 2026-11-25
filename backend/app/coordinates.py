import re
import warnings
from dataclasses import dataclass
from functools import lru_cache

import mgrs

GRID_ZONES = ("48Q", "49Q", "48P", "49P")
GRID_BOUNDS = {
    "48Q": (16.0, 24.0, 102.0, 108.0),
    "49Q": (16.0, 24.0, 108.0, 114.0),
    "48P": (8.0, 16.0, 102.0, 108.0),
    "49P": (8.0, 16.0, 108.0, 114.0),
}
_UTM_VALUE = re.compile(r"^[A-Z]{2}\d{6}$")
_CONVERTER = mgrs.MGRS()


@dataclass(frozen=True)
class ConvertedCoordinate:
    gzd: str
    mgrs: str
    latitude: float
    longitude: float


@lru_cache(maxsize=65_536)
def convert_to_latlong(source_utm: str | None) -> ConvertedCoordinate | None:
    """Resolve a SITRA grid reference by validating it against Vietnam's four GZDs."""
    if not source_utm:
        return None
    value = source_utm.strip().upper()
    if not _UTM_VALUE.fullmatch(value):
        return None

    matches: list[ConvertedCoordinate] = []
    for gzd in GRID_ZONES:
        mgrs_value = f"{gzd}{value}"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                latitude, longitude = _CONVERTER.toLatLon(mgrs_value)
        except mgrs.core.MGRSError:
            continue

        min_lat, max_lat, min_lon, max_lon = GRID_BOUNDS[gzd]
        if min_lat <= latitude < max_lat and min_lon <= longitude < max_lon:
            matches.append(
                ConvertedCoordinate(gzd, mgrs_value, latitude, longitude)
            )

    return matches[0] if len(matches) == 1 else None
