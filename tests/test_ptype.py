import pytest
import xarray as xr

from nesc_weather.ptype import ptype_mask, valid_ptype_mask, validate_ptype_values


def test_requested_ptype_groups_are_exact() -> None:
    ptype = xr.DataArray([0.0, 3.0, 6.0, 8.0, 12.0, float("nan")], dims="time")
    assert ptype_mask(ptype, "freezing_liquid").values.tolist() == [False, True, False, False, True, False]
    assert ptype_mask(ptype, "wet_snow").values.tolist() == [False, False, True, False, False, False]
    assert ptype_mask(ptype, "accretion_relevant").values.tolist() == [False, True, True, False, True, False]


def test_ptype_validation_rejects_interpolated_and_unknown_codes() -> None:
    with pytest.raises(ValueError, match="non-integral"):
        validate_ptype_values(xr.DataArray([3.5]))
    with pytest.raises(ValueError, match="unknown"):
        validate_ptype_values(xr.DataArray([99.0]))


def test_literal_wmo_missing_code_is_not_valid_data() -> None:
    ptype = xr.DataArray([0.0, 255.0, float("nan")])
    validate_ptype_values(ptype)
    assert valid_ptype_mask(ptype).values.tolist() == [True, False, False]
