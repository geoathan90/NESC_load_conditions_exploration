#!/usr/bin/env python3
"""Calculate the standard KPI families with Larisa restricted to the line-area ERA5 cells.

This is intentionally a focused companion to calculate_kpis.py.

Hard-coded Larisa spatial bounds:
    latitude:  39.50 to 40.00 degrees N
    longitude: 22.00 to 22.75 degrees E

On the current 0.25-degree Larisa ERA5 grid this selects 12 cells:
    latitudes:  39.50, 39.75, 40.00
    longitudes: 22.00, 22.25, 22.50, 22.75

Montana is left unchanged.

Run from the repository root:
    python scripts/calculate_kpis_focused_larisa_region.py

The existing KPI CLI options are preserved. No spatial CLI options are exposed;
the Larisa bounds above are deliberately hard-coded.

Default outputs:
    derived/kpis_focused_larisa_region/kpi_comparison.csv
    derived/kpis_focused_larisa_region/kpi_long.csv
    derived/kpis_focused_larisa_region/kpi_run_metadata.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np

import calculate_kpis as base

LARISA_LAT_MIN = 39.50
LARISA_LAT_MAX = 40.00
LARISA_LON_MIN = 22.00
LARISA_LON_MAX = 22.75
EXPECTED_LARISA_CELL_COUNT = 12


def _normalise_longitudes(longitudes: np.ndarray) -> np.ndarray:
    """Normalise longitude values to [-180, 180)."""
    return ((np.asarray(longitudes, dtype=np.float64) + 180.0) % 360.0) - 180.0


def _crop_field(
    field: np.ndarray,
    latitude_mask: np.ndarray,
    longitude_mask: np.ndarray,
) -> np.ndarray:
    """Crop a (time, latitude, longitude) ERA5 field."""
    array = np.asarray(field)
    if array.ndim != 3:
        raise ValueError(
            f"Expected a 3-D ERA5 field (time, latitude, longitude), got shape {array.shape}"
        )
    return array[:, latitude_mask, :][:, :, longitude_mask]


def process_region(
    config_path: Path,
    root: Path,
    freeze: float,
    wet_snow_max: float,
    gust_thr: float,
    snow_thr: float,
    start: int | None,
    end: int | None,
):
    """Run the normal KPI aggregation, spatially cropping Larisa only."""
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    original_name = cfg.get("display_name") or cfg["region"]
    is_larisa = original_name.strip().lower() == "larisa"
    output_name = "Larisa focused" if is_larisa else original_name

    y0 = int(cfg["years"]["start"])
    y1 = int(cfg["years"]["end"])
    if start is not None:
        y0 = max(y0, start)
    if end is not None:
        y1 = min(y1, end)
    if y1 < y0:
        raise ValueError(f"{output_name}: empty year range")

    a = base.Acc()
    selected_cell_count: int | None = None

    for year in range(y0, y1 + 1):
        paths = base.validate_year_files(root / str(year), year)

        with (
            h5py.File(paths["instant"], "r") as instant,
            h5py.File(paths["ptype"], "r") as pf,
            h5py.File(paths["avg"], "r") as avg,
            h5py.File(paths["max"], "r") as mx,
        ):
            t = base.kelvin_to_c(instant["t2m"][:])
            td = base.kelvin_to_c(instant["d2m"][:])
            tcslw = np.asarray(instant["tcslw"][:], dtype=np.float64)
            lcc = base.fraction_to_percent(instant["lcc"][:])
            cbh = np.asarray(instant["cbh"][:], dtype=np.float64)
            ptype = base.ptype_to_int(pf["ptype"][:])
            gust = np.asarray(mx["fg10"][:], dtype=np.float64)
            precip = base.rate_to_mmh(avg["avg_tprate"][:])
            snow = base.rate_to_mmh(avg["avg_tsrwe"][:])

            if is_larisa:
                latitudes = np.asarray(instant["latitude"][:], dtype=np.float64)
                longitudes = _normalise_longitudes(instant["longitude"][:])

                lat_mask = (
                    (latitudes >= LARISA_LAT_MIN)
                    & (latitudes <= LARISA_LAT_MAX)
                )
                lon_mask = (
                    (longitudes >= LARISA_LON_MIN)
                    & (longitudes <= LARISA_LON_MAX)
                )

                year_cell_count = int(np.count_nonzero(lat_mask) * np.count_nonzero(lon_mask))
                if year_cell_count != EXPECTED_LARISA_CELL_COUNT:
                    raise ValueError(
                        f"Larisa {year}: focused bounds selected {year_cell_count} cells; "
                        f"expected {EXPECTED_LARISA_CELL_COUNT}. "
                        "Check the ERA5 grid coordinates."
                    )

                if selected_cell_count is None:
                    selected_cell_count = year_cell_count

                t = _crop_field(t, lat_mask, lon_mask)
                td = _crop_field(td, lat_mask, lon_mask)
                tcslw = _crop_field(tcslw, lat_mask, lon_mask)
                lcc = _crop_field(lcc, lat_mask, lon_mask)
                cbh = _crop_field(cbh, lat_mask, lon_mask)
                ptype = _crop_field(ptype, lat_mask, lon_mask)
                gust = _crop_field(gust, lat_mask, lon_mask)
                precip = _crop_field(precip, lat_mask, lon_mask)
                snow = _crop_field(snow, lat_mask, lon_mask)

        a.total += int(t.size)
        dp = t - td

        fr_ptype = np.isin(ptype, base.FREEZING_LIQUID_CODES)
        fr = fr_ptype & (t <= freeze)
        a.fr_ptype += int(np.count_nonzero(fr_ptype))
        a.fr += int(np.count_nonzero(fr))
        if np.any(fr):
            x = precip[fr]
            a.fr_precip_s.add(x)
            a.fr_precip_q.add(x)

            x = gust[fr]
            a.fr_gust_s.add(x)
            a.fr_high += int(np.count_nonzero(x >= gust_thr))

            a.fr_temp_s.add(t[fr])

        wet_all = ptype == base.WET_SNOW_CODE
        wet = wet_all & (t <= wet_snow_max)

        wet_le_0 = wet_all & (t <= 0.0)
        wet_0_to_1 = wet_all & (t > 0.0) & (t <= 1.0)
        wet_1_to_2 = wet_all & (t > 1.0) & (t <= 2.0)
        wet_gt_2 = wet_all & (t > 2.0)

        a.wet_all += int(np.count_nonzero(wet_all))
        a.wet += int(np.count_nonzero(wet))
        a.wet_le_0 += int(np.count_nonzero(wet_le_0))
        a.wet_0_to_1 += int(np.count_nonzero(wet_0_to_1))
        a.wet_1_to_2 += int(np.count_nonzero(wet_1_to_2))
        a.wet_gt_2 += int(np.count_nonzero(wet_gt_2))

        if np.any(wet):
            x = snow[wet]
            a.wet_swe_s.add(x)
            a.wet_swe_q.add(x)

            a.wet_precip_s.add(precip[wet])

            x = gust[wet]
            a.wet_gust_s.add(x)
            a.wet_high += int(np.count_nonzero(x >= gust_thr))

        cold = t <= freeze
        a.cold += int(np.count_nonzero(cold))
        if np.any(cold):
            x = lcc[cold]
            a.cold_lcc_s.add(x)
            a.cold_lcc_q.add(x)

            x = cbh[cold]
            x = x[np.isfinite(x)]
            a.cold_cbh_valid += int(x.size)
            a.cold_cbh_q.add(x)

            x = tcslw[cold]
            a.cold_tcslw_s.add(x)
            a.cold_tcslw_q.add(x)

            a.cold_dp_q.add(dp[cold])

        a.temp_s.add(t)
        a.temp_q.add(t)
        a.dp_q.add(dp)

        snowy = snow > snow_thr
        a.snowy += int(np.count_nonzero(snowy))
        if np.any(snowy):
            x = snow[snowy]
            a.snowy_s.add(x)
            a.snowy_q.add(x)

        high = gust >= gust_thr
        cold_high = high & cold
        a.high += int(np.count_nonzero(high))
        a.cold_high += int(np.count_nonzero(cold_high))

        if np.any(cold):
            cg = gust[cold]
            ct = t[cold]
            i = int(np.argmax(cg))
            if a.max_cold_gust is None or float(cg[i]) > a.max_cold_gust:
                a.max_cold_gust = float(cg[i])
                a.temp_at_max_cold_gust = float(ct[i])

        print(
            f"{output_name} {year}: processed {t.size:,} grid-cell-hours "
            f"(running {a.total:,})"
        )

    values = {
        "fr_ptype": a.fr_ptype,
        "fr": a.fr,
        "fr_pct": base.pct(a.fr, a.total),
        "fr_pct_ptype": base.pct(a.fr, a.fr_ptype),
        "fr_precip_mean": a.fr_precip_s.mean,
        "fr_precip_p95": a.fr_precip_q.p(95),
        "fr_precip_max": a.fr_precip_s.max,
        "fr_high": a.fr_high,
        "fr_high_pct": base.pct(a.fr_high, a.fr),
        "fr_gust_max": a.fr_gust_s.max,
        "fr_temp_min": a.fr_temp_s.min,
        "wet_all": a.wet_all,
        "wet": a.wet,
        "wet_pct": base.pct(a.wet, a.total),
        "wet_pct_ptype": base.pct(a.wet, a.wet_all),
        "wet_le_0": a.wet_le_0,
        "wet_0_to_1": a.wet_0_to_1,
        "wet_1_to_2": a.wet_1_to_2,
        "wet_gt_2": a.wet_gt_2,
        "wet_le_0_pct_ptype": base.pct(a.wet_le_0, a.wet_all),
        "wet_0_to_1_pct_ptype": base.pct(a.wet_0_to_1, a.wet_all),
        "wet_1_to_2_pct_ptype": base.pct(a.wet_1_to_2, a.wet_all),
        "wet_gt_2_pct_ptype": base.pct(a.wet_gt_2, a.wet_all),
        "wet_swe_mean": a.wet_swe_s.mean,
        "wet_swe_p95": a.wet_swe_q.p(95),
        "wet_swe_max": a.wet_swe_s.max,
        "wet_precip_mean": a.wet_precip_s.mean,
        "wet_high": a.wet_high,
        "wet_high_pct": base.pct(a.wet_high, a.wet),
        "wet_gust_max": a.wet_gust_s.max,
        "cold": a.cold,
        "cold_pct": base.pct(a.cold, a.total),
        "lcc_mean": a.cold_lcc_s.mean,
        "lcc_p75": a.cold_lcc_q.p(75),
        "lcc_p90": a.cold_lcc_q.p(90),
        "cbh_valid_pct": base.pct(a.cold_cbh_valid, a.cold),
        "cbh_p50": a.cold_cbh_q.p(50),
        "cbh_p25": a.cold_cbh_q.p(25),
        "cbh_p05": a.cold_cbh_q.p(5),
        "tcslw_mean": a.cold_tcslw_s.mean,
        "tcslw_p95": a.cold_tcslw_q.p(95),
        "tcslw_p99": a.cold_tcslw_q.p(99),
        "tcslw_max": a.cold_tcslw_s.max,
        "cold_dp_p50": a.cold_dp_q.p(50),
        "temp_mean": a.temp_s.mean,
        "temp_p05": a.temp_q.p(5),
        "temp_min": a.temp_s.min,
        "dp_p50": a.dp_q.p(50),
        "dp_p25": a.dp_q.p(25),
        "dp_p05": a.dp_q.p(5),
        "snowy": a.snowy,
        "snowy_pct": base.pct(a.snowy, a.total),
        "snowy_mean": a.snowy_s.mean,
        "snowy_p95": a.snowy_q.p(95),
        "snowy_max": a.snowy_s.max,
        "high": a.high,
        "high_pct": base.pct(a.high, a.total),
        "cold_high": a.cold_high,
        "cold_high_pct": base.pct(a.cold_high, a.total),
        "cold_pct_high": base.pct(a.cold_high, a.high),
        "max_cold_gust": a.max_cold_gust,
        "temp_at_max_cold_gust": a.temp_at_max_cold_gust,
    }

    meta = {
        "region": output_name,
        "source_region": original_name,
        "config": str(config_path),
        "input_root": str(root),
        "years": {"start": y0, "end": y1},
        "total_grid_cell_hours": a.total,
    }

    if is_larisa:
        meta["spatial_filter"] = {
            "latitude_min": LARISA_LAT_MIN,
            "latitude_max": LARISA_LAT_MAX,
            "longitude_min": LARISA_LON_MIN,
            "longitude_max": LARISA_LON_MAX,
            "selected_grid_cells": selected_cell_count,
            "selection_type": "hard-coded rectangular ERA5 grid subset around transmission line",
        }

    return output_name, values, meta


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--dataset",
        action="append",
        nargs=2,
        metavar=("CONFIG", "INPUT_ROOT"),
        help="Repeatable dataset pair; defaults to project Montana + Larisa",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("derived/kpis_focused_larisa_region"),
    )
    p.add_argument("--freezing-temp-c", type=float, default=0.0)
    p.add_argument(
        "--wet-snow-temp-max-c",
        type=float,
        default=2.0,
        help="Maximum T2m for qualifying wet snow (default: 2.0 C)",
    )
    p.add_argument("--gust-threshold-ms", type=float, default=18.0)
    p.add_argument("--snowfall-threshold-mmh", type=float, default=0.0)
    p.add_argument("--start-year", type=int)
    p.add_argument("--end-year", type=int)
    args = p.parse_args()

    datasets = args.dataset or [
        ("config/montana.json", "data/raw/montana"),
        ("config/larisa.json", "data/raw/larisa"),
    ]

    results = {}
    region_meta = []

    for cfg, root in datasets:
        name, values, meta = process_region(
            Path(cfg),
            Path(root),
            args.freezing_temp_c,
            args.wet_snow_temp_max_c,
            args.gust_threshold_ms,
            args.snowfall_threshold_mmh,
            args.start_year,
            args.end_year,
        )
        if name in results:
            raise ValueError(f"Duplicate region name: {name}")
        results[name] = values
        region_meta.append(meta)

    metadata = {
        "method": (
            "Direct year-by-year validated NetCDF + NumPy aggregation; "
            "Larisa spatially restricted to hard-coded transmission-line-area bounds"
        ),
        "cell_hour_definition": "one selected ERA5 grid cell at one hourly timestamp",
        "larisa_focused_bounds": {
            "latitude_min": LARISA_LAT_MIN,
            "latitude_max": LARISA_LAT_MAX,
            "longitude_min": LARISA_LON_MIN,
            "longitude_max": LARISA_LON_MAX,
            "expected_selected_grid_cells": EXPECTED_LARISA_CELL_COUNT,
        },
        "thresholds": {
            "freezing_temp_c": args.freezing_temp_c,
            "wet_snow_temp_max_c": args.wet_snow_temp_max_c,
            "gust_threshold_ms": args.gust_threshold_ms,
            "snowfall_threshold_mmh": args.snowfall_threshold_mmh,
            "freezing_liquid_ptype_codes": list(base.FREEZING_LIQUID_CODES),
            "wet_snow_ptype_code": base.WET_SNOW_CODE,
        },
        "percentiles": {
            "method": "numpy.percentile over all qualifying grid-cell-hours",
            "stored_quantile_dtype": "float32",
        },
        "regions": region_meta,
    }

    base.write_outputs(args.output_dir, results, metadata)


if __name__ == "__main__":
    main()
