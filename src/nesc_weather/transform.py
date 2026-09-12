"""Transform validated ERA5 fields into canonical database units."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from .validation import VALID_PTYPE_CODES

KELVIN_OFFSET = 273.15
RATE_TO_MMH = 3600.0


def kelvin_to_c(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) - KELVIN_OFFSET


def fraction_to_percent(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) * 100.0


def rate_to_mmh(values: np.ndarray) -> np.ndarray:
    """kg m^-2 s^-1 water-equivalent -> mm/h."""
    return np.asarray(values, dtype=np.float64) * RATE_TO_MMH


def ptype_to_int(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if np.isnan(values).any():
        raise ValueError("ptype contains NaN; expected ERA5 categorical code or 255")
    rounded = np.rint(values)
    if not np.allclose(values, rounded, rtol=0.0, atol=1e-6):
        raise ValueError("ptype contains non-integer-like values")
    result = rounded.astype(np.int16)
    bad = sorted(set(np.unique(result).tolist()).difference(VALID_PTYPE_CODES))
    if bad:
        raise ValueError(f"ptype contains invalid code(s): {bad}")
    return result


def epoch_seconds_to_iso_z(values: np.ndarray) -> list[str]:
    return [
        datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for value in values
    ]


def require_finite(name: str, values: np.ndarray) -> None:
    if not np.isfinite(values).all():
        count = int(np.size(values) - np.isfinite(values).sum())
        raise ValueError(f"{name} contains {count} non-finite value(s), but the database column is NOT NULL")
