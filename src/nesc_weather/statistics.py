"""Numerical summaries for the winter observation population."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
import xarray as xr

from .ptype import PTYPE_GROUPS, ptype_mask, valid_ptype_mask

ANALYSIS_VARIABLES: dict[str, str] = {
    "t2m_c": "degC",
    "dewpoint_depression_c": "degC",
    "precip_rate_mmh": "mm h-1",
    "snowfall_rate_mmh": "mm h-1 water equivalent",
    "fg10": "m s-1",
    "low_cloud_cover_pct": "percent",
    "tcslw": "kg m-2",
    "cbh": "m",
}


def numeric_summary(values: np.ndarray) -> dict[str, float | int]:
    """Calculate a stable set of finite-value distribution statistics."""

    array = np.asarray(values, dtype=float).reshape(-1)
    finite = array[np.isfinite(array)]
    result: dict[str, float | int] = {
        "count": int(finite.size),
        "missing_count": int(array.size - finite.size),
    }
    names = ("min", "p05", "p25", "median", "mean", "p75", "p90", "p95", "p99", "max")
    if finite.size == 0:
        result.update({name: np.nan for name in names})
        result["std"] = np.nan
        return result
    percentiles = np.percentile(finite, [5, 25, 50, 75, 90, 95, 99])
    result.update(
        {
            "min": float(np.min(finite)),
            "p05": float(percentiles[0]),
            "p25": float(percentiles[1]),
            "median": float(percentiles[2]),
            "mean": float(np.mean(finite)),
            "p75": float(percentiles[3]),
            "p90": float(percentiles[4]),
            "p95": float(percentiles[5]),
            "p99": float(percentiles[6]),
            "max": float(np.max(finite)),
            "std": float(np.std(finite)),
        }
    )
    return result


def condition_masks(ds: xr.Dataset) -> dict[str, xr.DataArray]:
    valid = valid_ptype_mask(ds["ptype"])
    return {
        "all_winter": valid,
        "freezing_liquid": ptype_mask(ds["ptype"], "freezing_liquid"),
        "wet_snow": ptype_mask(ds["ptype"], "wet_snow"),
        "accretion_relevant": ptype_mask(ds["ptype"], "accretion_relevant"),
    }


def conditional_statistics(ds: xr.Dataset) -> pd.DataFrame:
    """Compare distributions under the requested icing-relevant conditions."""

    rows: list[dict[str, object]] = []
    for condition, mask in condition_masks(ds).items():
        condition_count = int(mask.sum().item())
        for variable, units in ANALYSIS_VARIABLES.items():
            summary = numeric_summary(ds[variable].values[mask.values])
            rows.append(
                {
                    "condition": condition,
                    "condition_grid_cell_hours": condition_count,
                    "variable": variable,
                    "units": units,
                    **summary,
                }
            )
    return pd.DataFrame(rows)


def cold_frequency(ds: xr.Dataset, thresholds_c: Iterable[float]) -> pd.DataFrame:
    """Count temperature observations at or below configured thresholds."""

    temperature = ds["t2m_c"]
    denominator = int(temperature.notnull().sum().item())
    rows = []
    for threshold in thresholds_c:
        count = int((temperature <= float(threshold)).sum().item())
        rows.append(
            {
                "metric": f"t2m_at_or_below_{float(threshold):g}_c",
                "threshold_c": float(threshold),
                "count_grid_cell_hours": count,
                "denominator_grid_cell_hours": denominator,
                "percentage": 100.0 * count / denominator,
            }
        )
    return pd.DataFrame(rows)


def precipitation_type_occurrence(ds: xr.Dataset) -> pd.DataFrame:
    """Count ptype groups with explicit all-hour and precipitation denominators."""

    ptype = ds["ptype"]
    valid = valid_ptype_mask(ptype)
    precipitation = valid & (ptype != 0)
    all_denominator = int(valid.sum().item())
    precipitation_denominator = int(precipitation.sum().item())
    group_order = [
        "freezing_rain",
        "freezing_drizzle",
        "freezing_liquid",
        "wet_snow",
        "accretion_relevant",
        "rain",
        "ordinary_snow",
        "rain_and_snow",
        "ice_pellets",
        "thunderstorm",
        "no_precipitation",
    ]
    rows: list[dict[str, object]] = []
    for group in group_order:
        mask = ptype_mask(ptype, group)
        count = int(mask.sum().item())
        count_among_precip = int((mask & precipitation).sum().item())
        rows.append(
            {
                "category": group,
                "ptype_codes": ";".join(str(code) for code in PTYPE_GROUPS[group]),
                "count_grid_cell_hours": count,
                "all_valid_grid_cell_hours": all_denominator,
                "pct_of_all_valid_grid_cell_hours": 100.0 * count / all_denominator,
                "count_among_ptype_precipitation": count_among_precip,
                "ptype_precipitation_grid_cell_hours": precipitation_denominator,
                "pct_of_ptype_precipitation": (
                    100.0 * count_among_precip / precipitation_denominator
                    if precipitation_denominator
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def ptype_sensitivity(
    ds: xr.Dataset, thresholds_mmh: Iterable[float]
) -> pd.DataFrame:
    """Show how precipitation-rate cutoffs alter icing-relevant ptype counts."""

    groups = [
        "freezing_rain",
        "freezing_drizzle",
        "freezing_liquid",
        "wet_snow",
        "accretion_relevant",
    ]
    total = int(valid_ptype_mask(ds["ptype"]).sum().item())
    rows: list[dict[str, object]] = []
    for group in groups:
        base_mask = ptype_mask(ds["ptype"], group)
        base_count = int(base_mask.sum().item())
        for threshold in thresholds_mmh:
            retained = base_mask & (ds["precip_rate_mmh"] >= float(threshold))
            count = int(retained.sum().item())
            rows.append(
                {
                    "category": group,
                    "minimum_precip_rate_mmh": float(threshold),
                    "count_grid_cell_hours": count,
                    "unfiltered_category_count": base_count,
                    "pct_of_unfiltered_category_retained": (
                        100.0 * count / base_count if base_count else np.nan
                    ),
                    "pct_of_all_valid_grid_cell_hours": 100.0 * count / total,
                }
            )
    return pd.DataFrame(rows)


def ptype_diagnostics(ds: xr.Dataset) -> pd.DataFrame:
    """Quantify ptype/rate/2 m temperature combinations worth manual review."""

    rows: list[dict[str, object]] = []
    checks = {
        "freezing_liquid": {
            "zero_interval_mean_precip_rate": ds["precip_rate_mmh"] == 0,
            "precip_rate_below_0.01_mmh": ds["precip_rate_mmh"] < 0.01,
            "t2m_above_0_c": ds["t2m_c"] > 0,
            "t2m_above_2_c": ds["t2m_c"] > 2,
        },
        "wet_snow": {
            "zero_interval_mean_precip_rate": ds["precip_rate_mmh"] == 0,
            "precip_rate_below_0.01_mmh": ds["precip_rate_mmh"] < 0.01,
            "t2m_above_5_c": ds["t2m_c"] > 5,
        },
    }
    for category, category_checks in checks.items():
        base = ptype_mask(ds["ptype"], category)
        denominator = int(base.sum().item())
        for diagnostic, check in category_checks.items():
            count = int((base & check).sum().item())
            rows.append(
                {
                    "category": category,
                    "diagnostic": diagnostic,
                    "count_grid_cell_hours": count,
                    "category_grid_cell_hours": denominator,
                    "percentage_of_category": (
                        100.0 * count / denominator if denominator else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows)


def per_grid_cell_summary(
    ds: xr.Dataset, event_counts: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Create one map-friendly row per ERA5 cell without domain averaging first."""

    rows: list[dict[str, object]] = []
    for latitude in ds.latitude.values:
        for longitude in ds.longitude.values:
            cell = ds.sel(latitude=latitude, longitude=longitude)
            ptype = cell["ptype"]
            ptype_denominator = int(valid_ptype_mask(ptype).sum().item())
            temperature_denominator = int(cell["t2m_c"].notnull().sum().item())
            row: dict[str, object] = {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "timestamp_count": int(cell.sizes["valid_time"]),
            }
            for variable in ANALYSIS_VARIABLES:
                summary = numeric_summary(cell[variable].values)
                for statistic in ("mean", "median", "p05", "p95", "p99", "min", "max"):
                    row[f"{variable}_{statistic}"] = summary[statistic]
                row[f"{variable}_missing_count"] = summary["missing_count"]
            for threshold in (0.0, -5.0, -10.0):
                count = int((cell["t2m_c"] <= threshold).sum().item())
                label = str(int(abs(threshold))) if threshold != 0 else "0"
                row[f"t2m_at_or_below_minus_{label}_c_count" if threshold < 0 else "t2m_at_or_below_0_c_count"] = count
                row[f"t2m_at_or_below_minus_{label}_c_pct" if threshold < 0 else "t2m_at_or_below_0_c_pct"] = 100.0 * count / temperature_denominator
            for group in (
                "freezing_rain",
                "freezing_drizzle",
                "freezing_liquid",
                "wet_snow",
                "accretion_relevant",
            ):
                count = int(ptype_mask(ptype, group).sum().item())
                row[f"{group}_count"] = count
                row[f"{group}_pct_all_hours"] = 100.0 * count / ptype_denominator
            rows.append(row)
    result = pd.DataFrame(rows)
    if event_counts is not None and not event_counts.empty:
        result = result.merge(event_counts, on=["latitude", "longitude"], how="left")
        for column in ("event_count", "maximum_event_duration_hours"):
            result[column] = result[column].fillna(0).astype(int)
    return result.sort_values(["latitude", "longitude"], ascending=[False, True])


def spatial_domain_summary(cells: pd.DataFrame) -> pd.DataFrame:
    """Summarize selected per-cell metrics across the domain."""

    metrics = [
        "t2m_c_mean",
        "t2m_at_or_below_0_c_pct",
        "t2m_at_or_below_minus_5_c_pct",
        "t2m_at_or_below_minus_10_c_pct",
        "fg10_p95",
        "fg10_max",
        "precip_rate_mmh_mean",
        "precip_rate_mmh_max",
        "tcslw_mean",
        "tcslw_max",
        "freezing_liquid_pct_all_hours",
        "wet_snow_pct_all_hours",
        "accretion_relevant_pct_all_hours",
        "event_count",
        "maximum_event_duration_hours",
    ]
    rows = []
    for metric in metrics:
        if metric not in cells:
            continue
        values = pd.to_numeric(cells[metric], errors="coerce")
        rows.append(
            {
                "metric": metric,
                "cell_count": int(values.notna().sum()),
                "domain_min": values.min(),
                "domain_median": values.median(),
                "domain_mean": values.mean(),
                "domain_max": values.max(),
            }
        )
    return pd.DataFrame(rows)
