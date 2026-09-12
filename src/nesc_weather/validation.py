"""Validation helpers for the four-file ERA5 yearly input contract."""

from __future__ import annotations

from calendar import isleap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping

import h5py
import numpy as np

FILE_NAMES = {
    "instant": "data_stream-oper_stepType-instant.nc",
    "ptype": "data_stream-oper_stepType-ptype.nc",
    "avg": "data_stream-oper_stepType-avg.nc",
    "max": "data_stream-oper_stepType-max.nc",
}

EXPECTED_VARIABLES = {
    "instant": ("t2m", "d2m", "tcslw", "lcc", "cbh"),
    "ptype": ("ptype",),
    "avg": ("avg_tprate", "avg_tsrwe"),
    "max": ("fg10",),
}

EXPECTED_STEP_TYPES = {
    "instant": "instant",
    "ptype": "instant",
    "avg": "avg",
    "max": "max",
}

EXPECTED_UNITS = {
    "t2m": "K",
    "d2m": "K",
    "tcslw": "kg m**-2",
    "lcc": "(0 - 1)",
    "cbh": "m",
    "ptype": "(Code table 4.201)",
    "avg_tprate": "kg m**-2 s**-1",
    "avg_tsrwe": "kg m**-2 s**-1",
    "fg10": "m s**-1",
}

VALID_PTYPE_CODES = set(range(15)) | {255}


def _decode_attr(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.ndarray) and value.shape == (1,):
        return _decode_attr(value[0])
    return str(value)


def expected_djf_timestamps(year: int) -> np.ndarray:
    """Return expected Jan/Feb/Dec hourly UTC epoch seconds for one calendar year."""
    starts_and_hours = [
        (datetime(year, 1, 1, tzinfo=timezone.utc), 31 * 24),
        (datetime(year, 2, 1, tzinfo=timezone.utc), (29 if isleap(year) else 28) * 24),
        (datetime(year, 12, 1, tzinfo=timezone.utc), 31 * 24),
    ]
    out: list[int] = []
    for start, hours in starts_and_hours:
        out.extend(int((start + timedelta(hours=i)).timestamp()) for i in range(hours))
    return np.asarray(out, dtype=np.int64)


def normalize_longitudes(values: np.ndarray) -> np.ndarray:
    """Normalize longitudes to [-180, 180), preserving numerical ordering after sort."""
    values = np.asarray(values, dtype=np.float64)
    return ((values + 180.0) % 360.0) - 180.0


def validate_year_files(year_dir: Path, year: int) -> Mapping[str, Path]:
    """Validate file presence, variables, units, dimensions, coordinates and timestamps."""
    year_dir = Path(year_dir)
    paths = {group: year_dir / name for group, name in FILE_NAMES.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required ERA5 files:\n" + "\n".join(missing))

    reference_time: np.ndarray | None = None
    reference_lat: np.ndarray | None = None
    reference_lon: np.ndarray | None = None
    expected_time = expected_djf_timestamps(year)

    for group, path in paths.items():
        with h5py.File(path, "r") as handle:
            required = set(EXPECTED_VARIABLES[group]) | {"valid_time", "latitude", "longitude"}
            absent = sorted(required.difference(handle.keys()))
            if absent:
                raise ValueError(f"{path.name}: missing datasets {absent}")

            time_values = np.asarray(handle["valid_time"][:], dtype=np.int64)
            lat_values = np.asarray(handle["latitude"][:], dtype=np.float64)
            lon_values = normalize_longitudes(handle["longitude"][:])

            if not np.array_equal(time_values, expected_time):
                raise ValueError(
                    f"{path.name}: timestamps do not exactly match expected Jan/Feb/Dec {year} hourly sequence"
                )

            if reference_time is None:
                reference_time = time_values
                reference_lat = lat_values
                reference_lon = lon_values
            else:
                if not np.array_equal(time_values, reference_time):
                    raise ValueError(f"{path.name}: timestamps do not match the other yearly files")
                if not np.allclose(lat_values, reference_lat, rtol=0.0, atol=1e-10):
                    raise ValueError(f"{path.name}: latitude grid does not match the other yearly files")
                if not np.allclose(lon_values, reference_lon, rtol=0.0, atol=1e-10):
                    raise ValueError(f"{path.name}: longitude grid does not match after normalization")

            expected_shape = (len(time_values), len(lat_values), len(lon_values))
            for variable in EXPECTED_VARIABLES[group]:
                dataset = handle[variable]
                if dataset.shape != expected_shape:
                    raise ValueError(
                        f"{path.name}:{variable} shape {dataset.shape} != expected {expected_shape}"
                    )

                step_type = _decode_attr(dataset.attrs.get("GRIB_stepType", ""))
                if step_type != EXPECTED_STEP_TYPES[group]:
                    raise ValueError(
                        f"{path.name}:{variable} GRIB_stepType={step_type!r}; expected {EXPECTED_STEP_TYPES[group]!r}"
                    )

                units = _decode_attr(dataset.attrs.get("units", ""))
                expected_units = EXPECTED_UNITS[variable]
                if units != expected_units:
                    raise ValueError(
                        f"{path.name}:{variable} units={units!r}; expected {expected_units!r}"
                    )

    return paths
