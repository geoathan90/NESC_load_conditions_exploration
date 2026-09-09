import pandas as pd

from nesc_weather.report import _event_rows, _lower_tail_rows, _upper_tail_rows


def _conditional_frame() -> pd.DataFrame:
    rows = []
    variables = {
        "t2m_c": "degC",
        "dewpoint_depression_c": "degC",
        "cbh": "m",
        "precip_rate_mmh": "mm h-1",
        "snowfall_rate_mmh": "mm h-1 water equivalent",
        "fg10": "m s-1",
        "tcslw": "kg m-2",
    }
    for variable, units in variables.items():
        rows.append(
            {
                "condition": "all_winter",
                "variable": variable,
                "units": units,
                "count": 100,
                "missing_count": 0,
                "mean": 10.0,
                "median": 9.0,
                "p25": 5.0,
                "p05": 2.0,
                "min": -7.0,
                "p90": 20.0,
                "p95": 30.0,
                "p99": 40.0,
                "max": 99.0,
            }
        )
    return pd.DataFrame(rows)


def test_report_profiles_use_engineering_relevant_tail() -> None:
    conditional = _conditional_frame()

    lower = _lower_tail_rows(conditional, ("all_winter",))
    temperature = lower[0]
    assert temperature[-3:] == [5.0, 2.0, -7.0]
    assert 99.0 not in temperature

    upper = _upper_tail_rows(conditional, ("all_winter",))
    gust = next(row for row in upper if "gust" in row[1].lower())
    assert gust[-4:] == [20.0, 30.0, 40.0, 99.0]
    assert -7.0 not in gust


def test_event_rows_include_minimum_temperature() -> None:
    events = pd.DataFrame(
        [
            {
                "latitude": 39.75,
                "longitude": 22.25,
                "start": "2020-01-01T00:00:00",
                "duration_hours": 3,
                "ptype_labels": "wet_snow",
                "temperature_min_c": -2.5,
                "temperature_mean_c": -0.5,
                "gust_max_ms": 12.0,
                "precipitation_water_equivalent_mm": 4.0,
                "snowfall_water_equivalent_mm": 3.5,
                "tcslw_max_kgm2": 0.2,
            }
        ]
    )

    row = _event_rows(events)[0]
    assert row[4] == -2.5
    assert row[5] == -0.5
