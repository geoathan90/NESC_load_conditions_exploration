"""Grid-cell event detection that respects real hourly continuity."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from .ptype import PTYPE_LABELS, ptype_mask


def contiguous_true_runs(
    times: pd.DatetimeIndex, mask: np.ndarray
) -> list[np.ndarray]:
    """Return true-index runs, breaking at any non-hourly timestamp gap."""

    boolean = np.asarray(mask, dtype=bool)
    if boolean.ndim != 1 or boolean.size != times.size:
        raise ValueError("Event mask must be one-dimensional and match timestamps")
    true_indices = np.flatnonzero(boolean)
    if true_indices.size == 0:
        return []
    runs: list[list[int]] = [[int(true_indices[0])]]
    for index in true_indices[1:]:
        previous = runs[-1][-1]
        consecutive_index = int(index) == previous + 1
        consecutive_time = times[int(index)] - times[previous] == pd.Timedelta(hours=1)
        if consecutive_index and consecutive_time:
            runs[-1].append(int(index))
        else:
            runs.append([int(index)])
    return [np.asarray(run, dtype=int) for run in runs]


def _finite_stat(values: np.ndarray, function: str) -> float:
    array = np.asarray(values, dtype=float)
    if not np.isfinite(array).any():
        return np.nan
    return float(getattr(np, f"nan{function}")(array))


def detect_accretion_events(
    ds: xr.Dataset, minimum_duration_hours: int = 1
) -> pd.DataFrame:
    """Find consecutive accretion-relevant observations independently per cell."""

    if minimum_duration_hours < 1:
        raise ValueError("minimum_duration_hours must be at least 1")
    times = pd.DatetimeIndex(ds.valid_time.values)
    rows: list[dict[str, object]] = []
    event_number = 0
    for latitude in ds.latitude.values:
        for longitude in ds.longitude.values:
            cell = ds.sel(latitude=latitude, longitude=longitude)
            mask = ptype_mask(cell["ptype"], "accretion_relevant").values
            for indices in contiguous_true_runs(times, mask):
                if len(indices) < minimum_duration_hours:
                    continue
                event_number += 1
                event = cell.isel(valid_time=indices)
                codes_array = np.rint(event["ptype"].values).astype(int)
                codes, counts = np.unique(codes_array, return_counts=True)
                dominant = int(codes[np.argmax(counts)])
                start = times[indices[0]]
                last = times[indices[-1]]
                rows.append(
                    {
                        "event_id": f"E{event_number:05d}",
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "start": start.isoformat(),
                        "end": last.isoformat(),
                        "end_exclusive": (last + pd.Timedelta(hours=1)).isoformat(),
                        "duration_hours": int(len(indices)),
                        "ptype_codes": ";".join(str(code) for code in codes),
                        "ptype_labels": ";".join(PTYPE_LABELS[code] for code in codes),
                        "dominant_ptype_code": dominant,
                        "dominant_ptype_label": PTYPE_LABELS[dominant],
                        "freezing_liquid_hours": int(
                            ptype_mask(event["ptype"], "freezing_liquid").sum().item()
                        ),
                        "wet_snow_hours": int(
                            ptype_mask(event["ptype"], "wet_snow").sum().item()
                        ),
                        "temperature_mean_c": _finite_stat(event["t2m_c"].values, "mean"),
                        "temperature_min_c": _finite_stat(event["t2m_c"].values, "min"),
                        "temperature_max_c": _finite_stat(event["t2m_c"].values, "max"),
                        "gust_mean_ms": _finite_stat(event["fg10"].values, "mean"),
                        "gust_max_ms": _finite_stat(event["fg10"].values, "max"),
                        "precip_rate_mean_mmh": _finite_stat(
                            event["precip_rate_mmh"].values, "mean"
                        ),
                        "precip_rate_max_mmh": _finite_stat(
                            event["precip_rate_mmh"].values, "max"
                        ),
                        "precipitation_water_equivalent_mm": float(
                            event["precip_rate_mmh"].fillna(0).sum().item()
                        ),
                        "snowfall_rate_mean_mmh": _finite_stat(
                            event["snowfall_rate_mmh"].values, "mean"
                        ),
                        "snowfall_rate_max_mmh": _finite_stat(
                            event["snowfall_rate_mmh"].values, "max"
                        ),
                        "snowfall_water_equivalent_mm": float(
                            event["snowfall_rate_mmh"].fillna(0).sum().item()
                        ),
                        "tcslw_mean_kgm2": _finite_stat(event["tcslw"].values, "mean"),
                        "tcslw_max_kgm2": _finite_stat(event["tcslw"].values, "max"),
                    }
                )
    columns = [
        "event_id", "latitude", "longitude", "start", "end", "end_exclusive",
        "duration_hours", "ptype_codes", "ptype_labels", "dominant_ptype_code",
        "dominant_ptype_label", "freezing_liquid_hours", "wet_snow_hours",
        "temperature_mean_c", "temperature_min_c", "temperature_max_c",
        "gust_mean_ms", "gust_max_ms", "precip_rate_mean_mmh",
        "precip_rate_max_mmh", "precipitation_water_equivalent_mm",
        "snowfall_rate_mean_mmh", "snowfall_rate_max_mmh",
        "snowfall_water_equivalent_mm", "tcslw_mean_kgm2", "tcslw_max_kgm2",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["duration_hours", "gust_max_ms", "start"], ascending=[False, False, True]
    )


def event_counts_by_cell(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(
            columns=["latitude", "longitude", "event_count", "maximum_event_duration_hours"]
        )
    return (
        events.groupby(["latitude", "longitude"], as_index=False)
        .agg(
            event_count=("event_id", "count"),
            maximum_event_duration_hours=("duration_hours", "max"),
        )
    )
