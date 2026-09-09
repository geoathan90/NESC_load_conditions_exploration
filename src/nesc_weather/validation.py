"""Strict annual ERA5 package validation and safe step-type merging."""

from __future__ import annotations

import calendar
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from .ptype import validate_ptype_values

TIME_NAME = "valid_time"
SPATIAL_NAMES = ("latitude", "longitude")
EXPECTED_UNITS = {
    "t2m": "K",
    "d2m": "K",
    "ptype": "(Code table 4.201)",
    "tcslw": "kg m**-2",
    "lcc": "(0 - 1)",
    "cbh": "m",
    "fg10": "m s**-1",
    "avg_tprate": "kg m**-2 s**-1",
    "avg_tsrwe": "kg m**-2 s**-1",
}


def normalize_longitudes(values: np.ndarray) -> np.ndarray:
    """Normalize longitudes to [-180, 180), retaining exact numeric values."""

    array = np.asarray(values, dtype=float)
    return ((array + 180.0) % 360.0) - 180.0


def canonicalize_dataset(ds: xr.Dataset) -> xr.Dataset:
    """Normalize common coordinate names and longitude convention."""

    rename: dict[str, str] = {}
    for candidate in ("time", "date"):
        if candidate in ds.coords and TIME_NAME not in ds.coords:
            rename[candidate] = TIME_NAME
    for candidate in ("lat",):
        if candidate in ds.coords and "latitude" not in ds.coords:
            rename[candidate] = "latitude"
    for candidate in ("lon",):
        if candidate in ds.coords and "longitude" not in ds.coords:
            rename[candidate] = "longitude"
    if rename:
        ds = ds.rename(rename)
    if "longitude" in ds.coords:
        normalized = normalize_longitudes(ds["longitude"].values)
        if len(np.unique(normalized)) != len(normalized):
            raise ValueError("Longitude normalization produced duplicate coordinates")
        ds = ds.assign_coords(longitude=normalized).sortby("longitude")
    return ds


def expected_hourly_times(year: int, months: list[int]) -> pd.DatetimeIndex:
    """Build the exact hourly timestamp population for selected calendar months."""

    pieces: list[pd.DatetimeIndex] = []
    for month in sorted(set(months)):
        last_day = calendar.monthrange(year, month)[1]
        pieces.append(
            pd.date_range(
                f"{year:04d}-{month:02d}-01 00:00:00",
                f"{year:04d}-{month:02d}-{last_day:02d} 23:00:00",
                freq="h",
            )
        )
    combined = pieces[0]
    for piece in pieces[1:]:
        combined = combined.append(piece)
    return combined.sort_values()


def _unexpected_within_month_gaps(times: pd.DatetimeIndex) -> int:
    frame = pd.DataFrame({"time": times})
    frame["month"] = frame["time"].dt.to_period("M")
    total = 0
    for _, group in frame.groupby("month", sort=False):
        total += int((group["time"].diff().dropna() != pd.Timedelta(hours=1)).sum())
    return total


def _format_continuous_segments(times: pd.DatetimeIndex) -> str:
    breaks = np.flatnonzero(np.diff(times.values) != np.timedelta64(1, "h"))
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks, len(times) - 1]
    return ";".join(
        f"{times[start].isoformat()}..{times[end].isoformat()}"
        for start, end in zip(starts, ends, strict=True)
    )


def _unique_aux_values(ds: xr.Dataset, name: str) -> str:
    if name not in ds.coords:
        return ""
    values = np.asarray(ds[name].values).reshape(-1)
    return ";".join(sorted(str(value) for value in np.unique(values)))


def _load_dataset(path: Path) -> xr.Dataset:
    try:
        with xr.open_dataset(path, engine="h5netcdf") as opened:
            return canonicalize_dataset(opened.load())
    except Exception as exc:
        raise ValueError(f"Could not open NetCDF file {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_and_merge_year(
    year: int,
    paths: dict[str, Path],
    era5: dict[str, Any],
    region: dict[str, Any],
) -> tuple[xr.Dataset, list[dict[str, object]]]:
    """Validate all step-type files for one year and merge only on exact alignment."""

    expected_by_step = era5["variables_by_step_type"]
    months = [int(month) for month in era5["months"]]
    expected_times = expected_hourly_times(year, months)
    datasets: dict[str, xr.Dataset] = {}
    rows: list[dict[str, object]] = []

    for step_type, path in sorted(paths.items()):
        ds = _load_dataset(path)
        datasets[step_type] = ds
        missing_coords = [
            name for name in (TIME_NAME, *SPATIAL_NAMES) if name not in ds.coords
        ]
        if missing_coords:
            raise ValueError(
                f"{year} {step_type} missing coordinates: {', '.join(missing_coords)}"
            )
        expected_vars = set(expected_by_step[step_type])
        missing_vars = sorted(expected_vars - set(ds.data_vars))
        if missing_vars:
            raise ValueError(
                f"{year} {step_type} missing variables: {', '.join(missing_vars)}"
            )
        times = pd.DatetimeIndex(ds[TIME_NAME].values)
        if times.hasnans:
            raise ValueError(f"{year} {step_type} has invalid timestamps")
        if times.has_duplicates:
            raise ValueError(f"{year} {step_type} has duplicate timestamps")
        if not times.is_monotonic_increasing:
            raise ValueError(f"{year} {step_type} timestamps are not monotonic")
        actual_months = sorted(set(int(value) for value in times.month))
        exact_time_coverage = times.equals(expected_times)
        if not exact_time_coverage:
            missing_count = len(expected_times.difference(times))
            extra_count = len(times.difference(expected_times))
            raise ValueError(
                f"{year} {step_type} hourly coverage mismatch: "
                f"{missing_count} missing, {extra_count} unexpected timestamps"
            )
        latitudes = np.asarray(ds.latitude.values, dtype=float)
        longitudes = np.asarray(ds.longitude.values, dtype=float)
        spacing = float(region["grid_spacing_degrees"])
        if len(latitudes) > 1 and not np.allclose(np.abs(np.diff(latitudes)), spacing):
            raise ValueError(f"{year} {step_type} latitude spacing mismatch")
        if len(longitudes) > 1 and not np.allclose(np.abs(np.diff(longitudes)), spacing):
            raise ValueError(f"{year} {step_type} longitude spacing mismatch")
        if not np.isclose(latitudes.max(), float(region["north"])):
            raise ValueError(f"{year} {step_type} north bound mismatch")
        if not np.isclose(latitudes.min(), float(region["south"])):
            raise ValueError(f"{year} {step_type} south bound mismatch")
        if not np.isclose(longitudes.min(), float(region["west"])):
            raise ValueError(f"{year} {step_type} west bound mismatch")
        if not np.isclose(longitudes.max(), float(region["east"])):
            raise ValueError(f"{year} {step_type} east bound mismatch")

        missing_cells = {
            variable: int(
                ds[variable].isnull().sum().item()
                + ((ds[variable] == 255).sum().item() if variable == "ptype" else 0)
            )
            for variable in sorted(expected_vars)
        }
        for variable in sorted(expected_vars):
            if ds[variable].dims != (TIME_NAME, *SPATIAL_NAMES):
                raise ValueError(
                    f"{year} {step_type} {variable} dimensions are {ds[variable].dims}; "
                    f"expected {(TIME_NAME, *SPATIAL_NAMES)}"
                )
            actual_units = ds[variable].attrs.get("units")
            if actual_units != EXPECTED_UNITS[variable]:
                raise ValueError(
                    f"{year} {step_type} {variable} units are {actual_units!r}; "
                    f"expected {EXPECTED_UNITS[variable]!r}"
                )
            actual_step_type = ds[variable].attrs.get("GRIB_stepType")
            if actual_step_type != step_type:
                raise ValueError(
                    f"{year} {step_type} {variable} GRIB_stepType is "
                    f"{actual_step_type!r}; expected {step_type!r}"
                )
        rows.append(
            {
                "year": year,
                "step_type": step_type,
                "path": str(path),
                "file_size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "variables_expected": ";".join(sorted(expected_vars)),
                "variables_present": ";".join(sorted(ds.data_vars)),
                "missing_value_counts": ";".join(
                    f"{key}:{value}" for key, value in missing_cells.items()
                ),
                "variable_units": ";".join(
                    f"{variable}:{ds[variable].attrs['units']}"
                    for variable in sorted(expected_vars)
                ),
                "time_start": times.min().isoformat(),
                "time_end": times.max().isoformat(),
                "continuous_time_segments": _format_continuous_segments(times),
                "timestamp_count": len(times),
                "expected_timestamp_count": len(expected_times),
                "months_present": ";".join(str(value) for value in actual_months),
                "hourly_coverage_passed": exact_time_coverage,
                "unexpected_within_month_gaps": _unexpected_within_month_gaps(times),
                "latitude_count": len(latitudes),
                "longitude_count": len(longitudes),
                "latitude_values": ";".join(f"{value:g}" for value in latitudes),
                "longitude_values": ";".join(f"{value:g}" for value in longitudes),
                "expver_values": _unique_aux_values(ds, "expver"),
                "validation_passed": True,
            }
        )

    reference = datasets["instant"]
    for step_type, ds in datasets.items():
        for coordinate in (TIME_NAME, *SPATIAL_NAMES):
            if not np.array_equal(reference[coordinate].values, ds[coordinate].values):
                raise ValueError(
                    f"{year} {step_type} is not aligned with instant on {coordinate}"
                )
        for auxiliary in ("expver", "number"):
            if auxiliary in reference.coords or auxiliary in ds.coords:
                if auxiliary not in reference.coords or auxiliary not in ds.coords:
                    raise ValueError(
                        f"{year} auxiliary coordinate {auxiliary} is not present in all files"
                    )
                if not np.array_equal(reference[auxiliary].values, ds[auxiliary].values):
                    raise ValueError(
                        f"{year} {step_type} auxiliary coordinate {auxiliary} differs"
                    )

    selected = []
    for step_type, ds in datasets.items():
        selected.append(ds[list(expected_by_step[step_type])])
    merged = xr.merge(selected, join="exact", compat="equals")
    for auxiliary in ("expver", "number"):
        if auxiliary in reference.coords:
            merged = merged.assign_coords({auxiliary: reference[auxiliary]})
    validate_ptype_values(merged["ptype"])
    return merged, rows


def validate_archive(
    year_files: dict[int, dict[str, Path]],
    era5: dict[str, Any],
    region: dict[str, Any],
) -> tuple[xr.Dataset, pd.DataFrame]:
    """Validate every year, enforce cross-year grid consistency, and concatenate."""

    annual: list[xr.Dataset] = []
    rows: list[dict[str, object]] = []
    reference_grid: tuple[np.ndarray, np.ndarray] | None = None
    for year, paths in sorted(year_files.items()):
        dataset, year_rows = validate_and_merge_year(year, paths, era5, region)
        grid = (dataset.latitude.values, dataset.longitude.values)
        if reference_grid is None:
            reference_grid = grid
        elif not (
            np.array_equal(reference_grid[0], grid[0])
            and np.array_equal(reference_grid[1], grid[1])
        ):
            raise ValueError(f"Year {year} grid differs from earlier years")
        annual.append(dataset)
        rows.extend(year_rows)

    combined = xr.concat(
        annual,
        dim=TIME_NAME,
        data_vars="all",
        coords="minimal",
        compat="equals",
        join="exact",
    ).sortby(TIME_NAME)
    times = pd.DatetimeIndex(combined[TIME_NAME].values)
    if times.has_duplicates:
        raise ValueError("Combined archive contains duplicate timestamps")
    return combined, pd.DataFrame(rows)
