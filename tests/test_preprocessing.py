import numpy as np
import xarray as xr

from nesc_weather.preprocessing import derive_analysis_variables, kelvin_to_celsius, water_flux_to_mmh


def test_unit_conversions() -> None:
    values = xr.DataArray([273.15, 274.15])
    np.testing.assert_allclose(kelvin_to_celsius(values), [0.0, 1.0])
    np.testing.assert_allclose(water_flux_to_mmh(xr.DataArray([0.0, 0.001])), [0.0, 3.6])


def test_derived_variables_preserve_raw_inputs() -> None:
    ds = xr.Dataset(
        {
            "t2m": ("x", [274.15]),
            "d2m": ("x", [273.15]),
            "avg_tprate": ("x", [0.001]),
            "avg_tsrwe": ("x", [0.0005]),
            "lcc": ("x", [0.25]),
        }
    )
    result = derive_analysis_variables(ds)
    assert "t2m" in result
    assert result.t2m_c.item() == 1.0
    assert result.d2m_c.item() == 0.0
    assert result.dewpoint_depression_c.item() == 1.0
    assert result.precip_rate_mmh.item() == 3.6
    assert result.snowfall_rate_mmh.item() == 1.8
    assert result.low_cloud_cover_pct.item() == 25.0
