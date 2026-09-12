from calendar import isleap

import numpy as np
import pytest

from nesc_weather.transform import kelvin_to_c, ptype_to_int, rate_to_mmh
from nesc_weather.validation import expected_djf_timestamps, normalize_longitudes


def test_basic_unit_conversions():
    assert kelvin_to_c(np.array([273.15]))[0] == pytest.approx(0.0)
    assert rate_to_mmh(np.array([1.0e-3]))[0] == pytest.approx(3.6)


def test_ptype_requires_integer_valid_codes():
    assert ptype_to_int(np.array([0.0, 3.0, 12.0, 255.0])).tolist() == [0, 3, 12, 255]
    with pytest.raises(ValueError):
        ptype_to_int(np.array([3.25]))
    with pytest.raises(ValueError):
        ptype_to_int(np.array([99.0]))


def test_longitude_normalization_handles_montana_convention():
    values = normalize_longitudes(np.array([242.0, 249.0]))
    assert values.tolist() == pytest.approx([-118.0, -111.0])


def test_expected_djf_hour_count():
    assert len(expected_djf_timestamps(1991)) == 2160
    assert len(expected_djf_timestamps(1992)) == 2184
    assert isleap(1992)
