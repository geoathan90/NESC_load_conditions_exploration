#!/usr/bin/env python3
"""Generate QGIS-ready climatological rasters for the freezing-liquid KPI family.

No yearly rasters are written. Yearly per-cell frequency metrics are calculated in
memory and reduced across the selected years. Conditional meteorological metrics
are reduced across all qualifying freezing-liquid cell-hours in the selected period.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import h5py
import numpy as np
import rasterio
from rasterio.transform import from_origin

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nesc_weather.transform import kelvin_to_c, ptype_to_int, rate_to_mmh
from nesc_weather.validation import normalize_longitudes, validate_year_files

FREEZING_LIQUID_CODES = (3, 12)
DEFAULT_FREEZING_TEMP_C = 0.0
DEFAULT_GUST_THRESHOLD_MS = 18.0
DEFAULT_STATS = ("mean", "median", "p95", "max")
AVAILABLE_STATS = ("mean", "median", "p05", "p95", "p99", "min", "max")


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    aggregation: str  # "annual" or "pooled"
    definition: str


METRICS: dict[str, MetricSpec] = {
    "fr_ptype_hours_per_year": MetricSpec(
        "fr_ptype_hours_per_year",
        "Freezing-liquid ptype hours per year",
        "hours/year",
        "annual",
        "Calendar-year Jan/Feb/Dec hours with ERA5 ptype in {3,12}, before temperature filtering.",
    ),
    "fr_hours_per_year": MetricSpec(
        "fr_hours_per_year",
        "Qualifying freezing-liquid hours per year",
        "hours/year",
        "annual",
        "Calendar-year Jan/Feb/Dec hours with ERA5 ptype in {3,12} and T2m <= freezing threshold.",
    ),
    "fr_share_pct": MetricSpec(
        "fr_share_pct",
        "Qualifying freezing-liquid share",
        "%",
        "annual",
        "Qualifying freezing-liquid hours divided by all Jan/Feb/Dec hours in each calendar year.",
    ),
    "fr_cold_share_ptype_pct": MetricSpec(
        "fr_cold_share_ptype_pct",
        "Cold share of freezing-liquid ptype",
        "%",
        "annual",
        "Qualifying freezing-liquid hours divided by all ptype {3,12} hours in each calendar year.",
    ),
    "fr_high_wind_hours_per_year": MetricSpec(
        "fr_high_wind_hours_per_year",
        "High-wind freezing-liquid hours per year",
        "hours/year",
        "annual",
        "Qualifying freezing-liquid hours with fg10 >= gust threshold, counted per calendar year.",
    ),
    "fr_high_wind_share_pct": MetricSpec(
        "fr_high_wind_share_pct",
        "High-wind share of freezing-liquid conditions",
        "%",
        "annual",
        "High-wind qualifying freezing-liquid hours divided by all qualifying freezing-liquid hours in each calendar year.",
    ),
    "fr_precip_rate_mmh": MetricSpec(
        "fr_precip_rate_mmh",
        "Precipitation rate during freezing-liquid conditions",
        "mm/h",
        "pooled",
        "avg_tprate across all qualifying freezing-liquid cell-hours in the full selected period.",
    ),
    "fr_gust_ms": MetricSpec(
        "fr_gust_ms",
        "10 m gust during freezing-liquid conditions",
        "m/s",
        "pooled",
        "fg10 across all qualifying freezing-liquid cell-hours in the full selected period.",
    ),
    "fr_temperature_c": MetricSpec(
        "fr_temperature_c",
        "2 m temperature during freezing-liquid conditions",
        "degC",
        "pooled",
        "T2m across all qualifying freezing-liquid cell-hours in the full selected period.",
    ),
}


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    out = np.full(np.asarray(numerator).shape, np.nan, dtype=np.float64)
    np.divide(
        np.asarray(numerator, dtype=np.float64),
        np.asarray(denominator, dtype=np.float64),
        out=out,
        where=np.asarray(denominator) != 0,
    )
    return out


def _sort_grid(
    latitudes: np.ndarray,
    longitudes: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lat = np.asarray(latitudes, dtype=np.float64)
    lon = normalize_longitudes(longitudes)
    row_order = np.argsort(lat)[::-1]
    col_order = np.argsort(lon)
    return lat[row_order], lon[col_order], row_order, col_order


def _reorder_field(field: np.ndarray, row_order: np.ndarray, col_order: np.ndarray) -> np.ndarray:
    array = np.asarray(field)
    if array.ndim != 3:
        raise ValueError(f"Expected (time, latitude, longitude), got shape {array.shape}")
    return array[:, row_order, :][:, :, col_order]


def _grid_transform(latitudes: np.ndarray, longitudes: np.ndarray):
    if latitudes.size < 2 or longitudes.size < 2:
        raise ValueError("GeoTIFF export requires at least two latitude and longitude coordinates")

    lon_steps = np.diff(longitudes)
    lat_steps = np.diff(latitudes)
    dx = float(np.median(np.abs(lon_steps)))
    dy = float(np.median(np.abs(lat_steps)))
    if dx <= 0 or dy <= 0:
        raise ValueError("Invalid ERA5 grid spacing")
    if not np.allclose(np.abs(lon_steps), dx, rtol=0.0, atol=1e-8):
        raise ValueError("Longitude grid is not uniformly spaced")
    if not np.allclose(np.abs(lat_steps), dy, rtol=0.0, atol=1e-8):
        raise ValueError("Latitude grid is not uniformly spaced")

    west = float(longitudes[0] - dx / 2.0)
    north = float(latitudes[0] + dy / 2.0)
    return from_origin(west, north, dx, dy)


def _nan_reduce(stack: np.ndarray, statistic: str, axis: int = 0) -> np.ndarray:
    functions: dict[str, Callable[..., np.ndarray]] = {
        "mean": np.nanmean,
        "median": np.nanmedian,
        "min": np.nanmin,
        "max": np.nanmax,
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        if statistic in functions:
            return np.asarray(functions[statistic](stack, axis=axis), dtype=np.float64)
        if statistic.startswith("p") and statistic[1:].isdigit():
            percentile = float(statistic[1:])
            return np.asarray(np.nanpercentile(stack, percentile, axis=axis), dtype=np.float64)
    raise ValueError(f"Unsupported statistic: {statistic}")


def _reduce_pooled_cells(
    chunks_by_cell: list[list[np.ndarray]],
    statistic: str,
    shape: tuple[int, int],
) -> np.ndarray:
    out = np.full(shape[0] * shape[1], np.nan, dtype=np.float64)
    for index, chunks in enumerate(chunks_by_cell):
        if not chunks:
            continue
        values = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        if values.size == 0:
            continue
        if statistic == "mean":
            out[index] = float(np.mean(values, dtype=np.float64))
        elif statistic == "median":
            out[index] = float(np.median(values))
        elif statistic == "min":
            out[index] = float(np.min(values))
        elif statistic == "max":
            out[index] = float(np.max(values))
        elif statistic.startswith("p") and statistic[1:].isdigit():
            out[index] = float(np.percentile(values, float(statistic[1:])))
        else:
            raise ValueError(f"Unsupported statistic: {statistic}")
    return out.reshape(shape)


def _append_pooled(
    chunks_by_cell: list[list[np.ndarray]],
    values: np.ndarray,
    mask: np.ndarray,
) -> None:
    value_cells = np.asarray(values).reshape(values.shape[0], -1)
    mask_cells = np.asarray(mask, dtype=bool).reshape(mask.shape[0], -1)
    active_cells = np.flatnonzero(np.any(mask_cells, axis=0))
    for index in active_cells:
        selected = value_cells[:, index][mask_cells[:, index]]
        selected = selected[np.isfinite(selected)]
        if selected.size:
            chunks_by_cell[int(index)].append(np.asarray(selected, dtype=np.float32))


def _write_geotiff(
    path: Path,
    data: np.ndarray,
    transform,
    metric: MetricSpec,
    statistic: str,
    metadata: dict[str, str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    array = np.asarray(data, dtype=np.float32)
    profile = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "compress": "DEFLATE",
        "predictor": 3,
        "nodata": np.nan,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array, 1)
        dst.set_band_description(1, f"{metric.label} - {statistic}")
        dst.update_tags(
            metric_key=metric.key,
            metric=metric.label,
            unit=metric.unit,
            statistic=statistic,
            aggregation=metric.aggregation,
            definition=metric.definition,
            **metadata,
        )


def _resolve_selected(
    values: list[str] | None,
    available: tuple[str, ...] | list[str],
    default: tuple[str, ...],
) -> list[str]:
    if not values:
        return list(default)
    if "all" in values:
        return list(available)
    return list(dict.fromkeys(values))


def _available_region_names() -> list[str]:
    return sorted(path.stem for path in (REPO_ROOT / "config").glob("*.json"))


def build_rasters(args: argparse.Namespace) -> list[Path]:
    if args.config is not None:
        config_path = _repo_path(args.config)
    else:
        if not args.region:
            raise ValueError("Specify --region or --config")
        config_path = REPO_ROOT / "config" / f"{args.region}.json"

    if not config_path.is_file():
        available = ", ".join(_available_region_names()) or "none"
        raise FileNotFoundError(
            f"Config not found: {config_path}. Available config regions: {available}"
        )

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    region = str(cfg["region"])
    display_name = str(cfg.get("display_name") or region)
    input_root = (
        _repo_path(args.input_root)
        if args.input_root
        else REPO_ROOT / "data" / "raw" / region
    )
    output_root = _repo_path(args.output_root)
    output_dir = output_root / region / "freezing_liquid"

    y0 = int(cfg["years"]["start"])
    y1 = int(cfg["years"]["end"])
    if args.start_year is not None:
        y0 = max(y0, args.start_year)
    if args.end_year is not None:
        y1 = min(y1, args.end_year)
    if y1 < y0:
        raise ValueError(f"{display_name}: empty year range after CLI limits")
    years = list(range(y0, y1 + 1))

    selected_metrics = _resolve_selected(args.metric, list(METRICS), tuple(METRICS))
    selected_stats = _resolve_selected(args.stat, list(AVAILABLE_STATS), DEFAULT_STATS)
    metric_specs = [METRICS[key] for key in selected_metrics]
    annual_keys = [m.key for m in metric_specs if m.aggregation == "annual"]
    pooled_keys = [m.key for m in metric_specs if m.aggregation == "pooled"]

    annual_values: dict[str, list[np.ndarray]] = {key: [] for key in annual_keys}
    pooled_chunks: dict[str, list[list[np.ndarray]]] = {}

    reference_lat: np.ndarray | None = None
    reference_lon: np.ndarray | None = None
    transform = None

    for year in years:
        paths = validate_year_files(input_root / str(year), year)
        with (
            h5py.File(paths["instant"], "r") as instant,
            h5py.File(paths["ptype"], "r") as ptype_file,
            h5py.File(paths["avg"], "r") as avg_file,
            h5py.File(paths["max"], "r") as max_file,
        ):
            lat, lon, row_order, col_order = _sort_grid(
                instant["latitude"][:],
                instant["longitude"][:],
            )
            t = _reorder_field(
                kelvin_to_c(instant["t2m"][:]), row_order, col_order
            )
            ptype = _reorder_field(
                ptype_to_int(ptype_file["ptype"][:]), row_order, col_order
            )

            need_gust = bool(
                {
                    "fr_high_wind_hours_per_year",
                    "fr_high_wind_share_pct",
                    "fr_gust_ms",
                }
                & set(selected_metrics)
            )
            need_precip = "fr_precip_rate_mmh" in selected_metrics
            gust = (
                _reorder_field(
                    np.asarray(max_file["fg10"][:], dtype=np.float64),
                    row_order,
                    col_order,
                )
                if need_gust
                else None
            )
            precip = (
                _reorder_field(
                    rate_to_mmh(avg_file["avg_tprate"][:]), row_order, col_order
                )
                if need_precip
                else None
            )

        if reference_lat is None:
            reference_lat = lat
            reference_lon = lon
            transform = _grid_transform(lat, lon)
            cell_count = int(lat.size * lon.size)
            pooled_chunks = {
                key: [[] for _ in range(cell_count)] for key in pooled_keys
            }
        else:
            if not np.allclose(lat, reference_lat, rtol=0.0, atol=1e-10):
                raise ValueError(
                    f"{display_name} {year}: latitude grid differs from the first selected year"
                )
            if not np.allclose(lon, reference_lon, rtol=0.0, atol=1e-10):
                raise ValueError(
                    f"{display_name} {year}: longitude grid differs from the first selected year"
                )

        fr_ptype = np.isin(ptype, FREEZING_LIQUID_CODES)
        fr = fr_ptype & np.isfinite(t) & (t <= args.freezing_temp_c)
        n_hours = t.shape[0]

        fr_ptype_hours = np.count_nonzero(fr_ptype, axis=0).astype(np.float64)
        fr_hours = np.count_nonzero(fr, axis=0).astype(np.float64)

        if "fr_ptype_hours_per_year" in annual_values:
            annual_values["fr_ptype_hours_per_year"].append(fr_ptype_hours)
        if "fr_hours_per_year" in annual_values:
            annual_values["fr_hours_per_year"].append(fr_hours)
        if "fr_share_pct" in annual_values:
            annual_values["fr_share_pct"].append(100.0 * fr_hours / float(n_hours))
        if "fr_cold_share_ptype_pct" in annual_values:
            annual_values["fr_cold_share_ptype_pct"].append(
                100.0 * _safe_divide(fr_hours, fr_ptype_hours)
            )

        if gust is not None:
            high_wind = fr & np.isfinite(gust) & (gust >= args.gust_threshold_ms)
            high_hours = np.count_nonzero(high_wind, axis=0).astype(np.float64)
            if "fr_high_wind_hours_per_year" in annual_values:
                annual_values["fr_high_wind_hours_per_year"].append(high_hours)
            if "fr_high_wind_share_pct" in annual_values:
                annual_values["fr_high_wind_share_pct"].append(
                    100.0 * _safe_divide(high_hours, fr_hours)
                )
            if "fr_gust_ms" in pooled_chunks:
                _append_pooled(pooled_chunks["fr_gust_ms"], gust, fr)

        if precip is not None and "fr_precip_rate_mmh" in pooled_chunks:
            _append_pooled(pooled_chunks["fr_precip_rate_mmh"], precip, fr)
        if "fr_temperature_c" in pooled_chunks:
            _append_pooled(pooled_chunks["fr_temperature_c"], t, fr)

        print(
            f"{display_name} {year}: {int(np.count_nonzero(fr)):,} qualifying "
            f"freezing-liquid cell-hours"
        )

    if reference_lat is None or reference_lon is None or transform is None:
        raise RuntimeError("No years were processed")

    output_dir.mkdir(parents=True, exist_ok=True)
    raster_paths: list[Path] = []
    tag_metadata = {
        "region": display_name,
        "region_key": region,
        "year_start": str(y0),
        "year_end": str(y1),
        "year_count": str(len(years)),
        "freezing_temp_c": str(args.freezing_temp_c),
        "gust_threshold_ms": str(args.gust_threshold_ms),
        "ptype_codes": ",".join(str(code) for code in FREEZING_LIQUID_CODES),
        "crs_note": "ERA5 native latitude-longitude grid; no spatial interpolation",
    }

    for spec in metric_specs:
        for statistic in selected_stats:
            if spec.aggregation == "annual":
                stack = np.stack(annual_values[spec.key], axis=0)
                raster = _nan_reduce(stack, statistic, axis=0)
            else:
                raster = _reduce_pooled_cells(
                    pooled_chunks[spec.key],
                    statistic,
                    (reference_lat.size, reference_lon.size),
                )
            path = output_dir / f"{spec.key}_{statistic}.tif"
            _write_geotiff(path, raster, transform, spec, statistic, tag_metadata)
            raster_paths.append(path)
            shown = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
            print(f"Wrote {shown}")

    metadata = {
        "region": display_name,
        "region_key": region,
        "config": str(config_path),
        "input_root": str(input_root),
        "output_dir": str(output_dir),
        "years": {"start": y0, "end": y1, "count": len(years)},
        "thresholds": {
            "freezing_temp_c": args.freezing_temp_c,
            "gust_threshold_ms": args.gust_threshold_ms,
            "freezing_liquid_ptype_codes": list(FREEZING_LIQUID_CODES),
        },
        "statistics": selected_stats,
        "metrics": {
            spec.key: {
                "label": spec.label,
                "unit": spec.unit,
                "aggregation": spec.aggregation,
                "definition": spec.definition,
            }
            for spec in metric_specs
        },
        "spatial": {
            "crs": "EPSG:4326",
            "latitude_count": int(reference_lat.size),
            "longitude_count": int(reference_lon.size),
            "latitude_min": float(np.min(reference_lat)),
            "latitude_max": float(np.max(reference_lat)),
            "longitude_min": float(np.min(reference_lon)),
            "longitude_max": float(np.max(reference_lon)),
            "interpolation": "none",
        },
        "outputs": [str(path) for path in raster_paths],
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    shown_metadata = (
        metadata_path.relative_to(REPO_ROOT)
        if metadata_path.is_relative_to(REPO_ROOT)
        else metadata_path
    )
    print(f"Wrote {shown_metadata}")
    return raster_paths


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        help="Region key; resolves config/<region>.json and data/raw/<region>.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional config JSON override. If supplied, --region is not required.",
    )
    parser.add_argument(
        "--input-root", type=Path, help="Optional yearly NetCDF root override."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("raster_outputs"),
        help="Raster output root (default: raster_outputs).",
    )
    parser.add_argument(
        "--start-year", type=int, help="Optional lower year bound within the config range."
    )
    parser.add_argument(
        "--end-year", type=int, help="Optional upper year bound within the config range."
    )
    parser.add_argument(
        "--freezing-temp-c", type=float, default=DEFAULT_FREEZING_TEMP_C
    )
    parser.add_argument(
        "--gust-threshold-ms", type=float, default=DEFAULT_GUST_THRESHOLD_MS
    )
    parser.add_argument(
        "--metric",
        action="append",
        choices=[*METRICS, "all"],
        help="Metric to export; repeatable. Default: all freezing-liquid raster metrics.",
    )
    parser.add_argument(
        "--stat",
        action="append",
        choices=[*AVAILABLE_STATS, "all"],
        help="Statistic to export; repeatable. Default: mean, median, p95, max.",
    )
    parser.add_argument(
        "--list-metrics",
        action="store_true",
        help="Print available raster metrics and exit.",
    )
    parser.add_argument(
        "--list-regions",
        action="store_true",
        help="Print region keys currently available under config/ and exit.",
    )
    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    if args.list_metrics:
        for spec in METRICS.values():
            print(
                f"{spec.key:34s} {spec.aggregation:6s} "
                f"{spec.unit:12s} {spec.label}"
            )
        return
    if args.list_regions:
        for region in _available_region_names():
            print(region)
        return
    if args.region and args.config:
        parser.error("Use either --region or --config, not both")
    if not args.region and args.config is None:
        parser.error("Specify --region REGION or --config CONFIG")

    try:
        build_rasters(args)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
