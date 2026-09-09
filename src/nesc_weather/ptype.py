"""ECMWF precipitation-type codes and project-specific groupings."""

from __future__ import annotations

import numpy as np
import xarray as xr

# ECMWF GRIB2 Code Table 4.201. Codes 9--11 are reserved.
PTYPE_LABELS: dict[int, str] = {
    0: "no_precipitation",
    1: "rain",
    2: "thunderstorm",
    3: "freezing_rain",
    4: "mixed_or_ice",
    5: "snow",
    6: "wet_snow",
    7: "rain_and_snow",
    8: "ice_pellets",
    9: "graupel",
    10: "hail",
    11: "drizzle",
    12: "freezing_drizzle",
    13: "hail_less_than_5_mm",
    14: "hail_at_least_5_mm",
    255: "missing",
}

PTYPE_GROUPS: dict[str, tuple[int, ...]] = {
    "freezing_rain": (3,),
    "freezing_drizzle": (12,),
    "freezing_liquid": (3, 12),
    "wet_snow": (6,),
    "accretion_relevant": (3, 6, 12),
    "ordinary_snow": (5,),
    "ice_pellets": (8,),
    "rain": (1,),
    "rain_and_snow": (7,),
    "thunderstorm": (2,),
    "no_precipitation": (0,),
}


def validate_ptype_values(ptype: xr.DataArray) -> None:
    """Reject non-integral or unknown non-missing precipitation-type values."""

    values = np.asarray(ptype.values)
    finite = values[np.isfinite(values)]
    if not np.allclose(finite, np.rint(finite), atol=1e-6):
        sample = finite[np.abs(finite - np.rint(finite)) > 1e-6][:5]
        raise ValueError(f"ptype contains non-integral categorical values: {sample}")
    unknown = sorted(set(np.rint(finite).astype(int)) - PTYPE_LABELS.keys())
    if unknown:
        raise ValueError(f"ptype contains unknown ECMWF codes: {unknown}")


def ptype_mask(ptype: xr.DataArray, group: str) -> xr.DataArray:
    """Return a categorical mask without interpolating ptype."""

    try:
        codes = PTYPE_GROUPS[group]
    except KeyError as exc:
        raise KeyError(f"Unknown precipitation-type group: {group}") from exc
    return ptype.isin(codes).fillna(False)


def valid_ptype_mask(ptype: xr.DataArray) -> xr.DataArray:
    """Treat both decoded NaN and literal WMO code 255 as missing."""

    return (ptype.notnull() & (ptype != 255)).fillna(False)
