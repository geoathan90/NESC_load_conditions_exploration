"""Analysis-friendly derived variables with explicit units."""

from __future__ import annotations

import xarray as xr


def kelvin_to_celsius(values: xr.DataArray) -> xr.DataArray:
    return values - 273.15


def water_flux_to_mmh(values: xr.DataArray) -> xr.DataArray:
    """Convert kg m-2 s-1 water-equivalent flux to mm h-1."""

    return values * 3600.0


def derive_analysis_variables(ds: xr.Dataset) -> xr.Dataset:
    """Return raw variables plus consistently named, unit-aware derivatives."""

    result = ds.copy()
    result["t2m_c"] = kelvin_to_celsius(result["t2m"])
    result["t2m_c"].attrs.update(long_name="2 m temperature", units="degC")
    result["d2m_c"] = kelvin_to_celsius(result["d2m"])
    result["d2m_c"].attrs.update(long_name="2 m dewpoint temperature", units="degC")
    result["dewpoint_depression_c"] = result["t2m_c"] - result["d2m_c"]
    result["dewpoint_depression_c"].attrs.update(
        long_name="2 m temperature minus 2 m dewpoint", units="degC"
    )
    result["precip_rate_mmh"] = water_flux_to_mmh(result["avg_tprate"])
    result["precip_rate_mmh"].attrs.update(
        long_name="mean total precipitation rate", units="mm h-1"
    )
    result["snowfall_rate_mmh"] = water_flux_to_mmh(result["avg_tsrwe"])
    result["snowfall_rate_mmh"].attrs.update(
        long_name="mean total snowfall rate, water equivalent", units="mm h-1"
    )
    result["low_cloud_cover_pct"] = result["lcc"] * 100.0
    result["low_cloud_cover_pct"].attrs.update(
        long_name="low cloud cover", units="percent"
    )
    return result
