from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from nesc_weather.validation import (
    canonicalize_dataset,
    expected_hourly_times,
    normalize_longitudes,
    validate_and_merge_year,
)


ERA5 = {
    "months": [12, 1, 2],
    "variables_by_step_type": {
        "instant": ["t2m", "d2m", "ptype", "tcslw", "lcc", "cbh"],
        "avg": ["avg_tprate", "avg_tsrwe"],
        "max": ["fg10"],
    },
}
REGION = {
    "north": 40.25,
    "south": 39.25,
    "west": 21.75,
    "east": 22.75,
    "grid_spacing_degrees": 0.25,
}


def _write_year(
    tmp_path: Path,
    year: int = 2013,
    misalign_max: bool = False,
    ) -> dict[str, Path]:

    times = expected_hourly_times(year, ERA5["months"])
    times = expected_hourly_times(2013, ERA5["months"])
    lat = [40.25, 40.0, 39.75, 39.5, 39.25]
    lon = [21.75, 22.0, 22.25, 22.5, 22.75]
    shape = (len(times), len(lat), len(lon))
    coords = {
        "valid_time": times,
        "latitude": lat,
        "longitude": lon,
        "expver": ("valid_time", np.repeat("0001", len(times))),
        "number": 0,
    }
    arrays = lambda value: np.full(shape, value, dtype=np.float32)
    datasets = {
        "instant": xr.Dataset(
            {
                "t2m": (("valid_time", "latitude", "longitude"), arrays(273.15)),
                "d2m": (("valid_time", "latitude", "longitude"), arrays(272.15)),
                "ptype": (("valid_time", "latitude", "longitude"), arrays(0)),
                "tcslw": (("valid_time", "latitude", "longitude"), arrays(0)),
                "lcc": (("valid_time", "latitude", "longitude"), arrays(0.5)),
                "cbh": (("valid_time", "latitude", "longitude"), arrays(1000)),
            },
            coords=coords,
        ),
        "avg": xr.Dataset(
            {
                "avg_tprate": (("valid_time", "latitude", "longitude"), arrays(0)),
                "avg_tsrwe": (("valid_time", "latitude", "longitude"), arrays(0)),
            },
            coords=coords,
        ),
        "max": xr.Dataset(
            {"fg10": (("valid_time", "latitude", "longitude"), arrays(5))},
            coords=coords,
        ),
    }
    units = {
        "t2m": "K",
        "d2m": "K",
        "ptype": "(Code table 4.201)",
        "tcslw": "kg m**-2",
        "lcc": "(0 - 1)",
        "cbh": "m",
        "avg_tprate": "kg m**-2 s**-1",
        "avg_tsrwe": "kg m**-2 s**-1",
        "fg10": "m s**-1",
    }
    for step_type, ds in datasets.items():
        for variable in ds.data_vars:
            ds[variable].attrs.update(units=units[variable], GRIB_stepType=step_type)
    if misalign_max:
        datasets["max"] = datasets["max"].assign_coords(longitude=np.asarray(lon) + 0.01)
    paths = {}
    for step_type, ds in datasets.items():
        path = tmp_path / f"{step_type}.nc"
        ds.to_netcdf(path, engine="h5netcdf")
        paths[step_type] = path
    return paths


def test_longitude_normalization_and_sorting() -> None:
    np.testing.assert_allclose(normalize_longitudes(np.array([242.0, 249.0])), [-118.0, -111.0])
    ds = xr.Dataset(coords={"longitude": [359.0, 1.0]})
    normalized = canonicalize_dataset(ds)
    np.testing.assert_allclose(normalized.longitude, [-1.0, 1.0])


def test_validation_merges_exactly_aligned_step_types(tmp_path: Path) -> None:
    merged, rows = validate_and_merge_year(2013, _write_year(tmp_path), ERA5, REGION)
    assert set(merged.data_vars) == set(sum(ERA5["variables_by_step_type"].values(), []))
    assert len(rows) == 3
    assert all(row["validation_passed"] for row in rows)
    assert all(row["unexpected_within_month_gaps"] == 0 for row in rows)
    assert all(row["continuous_time_segments"].count(";") == 1 for row in rows)


def test_validation_rejects_step_type_grid_misalignment(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bound mismatch|not aligned"):
        validate_and_merge_year(2013, _write_year(tmp_path, misalign_max=True), ERA5, REGION)

def test_validation_accepts_2012_leap_year(tmp_path: Path) -> None:
    merged, rows = validate_and_merge_year(
        2012,
        _write_year(tmp_path, year=2012),
        ERA5,
        REGION,
    )

    times = pd.DatetimeIndex(merged.valid_time.values)

    assert len(times) == 2184
    assert pd.Timestamp("2012-02-29 00:00:00") in times
    assert times[0] == pd.Timestamp("2012-01-01 00:00:00")
    assert times[-1] == pd.Timestamp("2012-12-31 23:00:00")

    assert len(rows) == 3
    assert all(row["timestamp_count"] == 2184 for row in rows)
    assert all(row["validation_passed"] for row in rows)
