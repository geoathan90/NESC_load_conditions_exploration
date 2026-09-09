import numpy as np
import pandas as pd
import pytest
import xarray as xr

from nesc_weather.events import contiguous_true_runs, detect_accretion_events


def test_true_runs_do_not_bridge_archive_gap() -> None:
    times = pd.DatetimeIndex(
        ["2020-02-29 22:00", "2020-02-29 23:00", "2020-12-01 00:00", "2020-12-01 01:00"]
    )
    runs = contiguous_true_runs(times, np.array([True, True, True, True]))
    assert [run.tolist() for run in runs] == [[0, 1], [2, 3]]


def test_event_detection_keeps_cells_separate_and_reports_variables() -> None:
    times = pd.DatetimeIndex(
        ["2020-02-29 22:00", "2020-02-29 23:00", "2020-12-01 00:00", "2020-12-01 01:00"]
    )
    shape = (4, 1, 1)
    def data(values: list[float]) -> tuple[tuple[str, ...], np.ndarray]:
        return (("valid_time", "latitude", "longitude"), np.asarray(values).reshape(shape))
    ds = xr.Dataset(
        {
            "ptype": data([3, 3, 6, 6]),
            "t2m_c": data([-1, -2, 0, 1]),
            "fg10": data([5, 6, 7, 8]),
            "precip_rate_mmh": data([0.1, 0.2, 0.3, 0.4]),
            "snowfall_rate_mmh": data([0, 0, 0.2, 0.3]),
            "tcslw": data([0.01, 0.02, 0.03, 0.04]),
        },
        coords={"valid_time": times, "latitude": [40.0], "longitude": [22.0]},
    )
    events = detect_accretion_events(ds)
    assert len(events) == 2
    assert events.duration_hours.tolist() == [2, 2]
    assert set(events.ptype_labels) == {"freezing_rain", "wet_snow"}
    assert sorted(events.precipitation_water_equivalent_mm.tolist()) == pytest.approx([0.3, 0.7])
