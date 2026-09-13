#!/usr/bin/env python3
"""Calculate Montana/Larisa KPI families directly from yearly ERA5 NetCDF files.

Run from the repository root:
    python scripts/calculate_kpis.py

Default outputs:
    derived/kpis/kpi_comparison.csv
    derived/kpis/kpi_long.csv
    derived/kpis/kpi_run_metadata.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nesc_weather.transform import fraction_to_percent, kelvin_to_c, ptype_to_int, rate_to_mmh
from nesc_weather.validation import validate_year_files

FREEZING_LIQUID_CODES = (3, 12)
WET_SNOW_CODE = 6


@dataclass
class Stats:
    count: int = 0
    total: float = 0.0
    minimum: float = math.inf
    maximum: float = -math.inf

    def add(self, x: np.ndarray) -> None:
        a = np.asarray(x)
        if a.size == 0:
            return
        a = a[np.isfinite(a)]
        if a.size == 0:
            return
        self.count += int(a.size)
        self.total += float(np.sum(a, dtype=np.float64))
        self.minimum = min(self.minimum, float(np.min(a)))
        self.maximum = max(self.maximum, float(np.max(a)))

    @property
    def mean(self):
        return self.total / self.count if self.count else None

    @property
    def min(self):
        return self.minimum if self.count else None

    @property
    def max(self):
        return self.maximum if self.count else None


@dataclass
class Q:
    chunks: list[np.ndarray] = field(default_factory=list)

    def add(self, x: np.ndarray) -> None:
        a = np.asarray(x)
        if a.size == 0:
            return
        a = a[np.isfinite(a)]
        if a.size:
            self.chunks.append(np.asarray(a, dtype=np.float32).copy())

    def p(self, percentile: float):
        if not self.chunks:
            return None
        a = self.chunks[0] if len(self.chunks) == 1 else np.concatenate(self.chunks)
        return float(np.percentile(a, percentile))


@dataclass
class Acc:
    total: int = 0
    fr_ptype: int = 0
    fr: int = 0
    fr_high: int = 0
    fr_precip_s: Stats = field(default_factory=Stats)
    fr_precip_q: Q = field(default_factory=Q)
    fr_gust_s: Stats = field(default_factory=Stats)
    fr_temp_s: Stats = field(default_factory=Stats)

    wet_all: int = 0
    wet: int = 0
    wet_high: int = 0
    wet_swe_s: Stats = field(default_factory=Stats)
    wet_swe_q: Q = field(default_factory=Q)
    wet_precip_s: Stats = field(default_factory=Stats)
    wet_gust_s: Stats = field(default_factory=Stats)

    cold: int = 0
    cold_lcc_s: Stats = field(default_factory=Stats)
    cold_lcc_q: Q = field(default_factory=Q)
    cold_cbh_valid: int = 0
    cold_cbh_q: Q = field(default_factory=Q)
    cold_tcslw_s: Stats = field(default_factory=Stats)
    cold_tcslw_q: Q = field(default_factory=Q)
    cold_dp_q: Q = field(default_factory=Q)

    temp_s: Stats = field(default_factory=Stats)
    temp_q: Q = field(default_factory=Q)
    dp_q: Q = field(default_factory=Q)
    snowy: int = 0
    snowy_s: Stats = field(default_factory=Stats)
    snowy_q: Q = field(default_factory=Q)

    high: int = 0
    cold_high: int = 0
    max_cold_gust: float | None = None
    temp_at_max_cold_gust: float | None = None


@dataclass(frozen=True)
class Metric:
    family: str
    key: str
    label: str
    unit: str
    denominator: str
    definition: str


M = (
    Metric("1A Freezing liquid", "fr_ptype", "Freezing-liquid ptype cell-hours, all temperatures", "cell-hours", "all DJF grid-cell-hours", "ptype in {3,12}, before temperature filtering"),
    Metric("1A Freezing liquid", "fr", "Qualifying freezing-liquid cell-hours", "cell-hours", "all DJF grid-cell-hours", "ptype in {3,12} and T2m <= freezing threshold"),
    Metric("1A Freezing liquid", "fr_pct", "Qualifying freezing-liquid share", "%", "all DJF grid-cell-hours", "qualifying freezing-liquid cell-hours / all grid-cell-hours"),
    Metric("1A Freezing liquid", "fr_pct_ptype", "Cold share of freezing-liquid ptype", "%", "ptype {3,12} cell-hours", "qualifying / all ptype {3,12}"),
    Metric("1A Freezing liquid", "fr_precip_mean", "Mean precipitation rate", "mm/h", "qualifying freezing-liquid cell-hours", "mean avg_tprate"),
    Metric("1A Freezing liquid", "fr_precip_p95", "P95 precipitation rate", "mm/h", "qualifying freezing-liquid cell-hours", "95th percentile avg_tprate"),
    Metric("1A Freezing liquid", "fr_precip_max", "Maximum precipitation rate", "mm/h", "qualifying freezing-liquid cell-hours", "maximum avg_tprate"),
    Metric("1A Freezing liquid", "fr_high", "High-wind freezing-liquid cell-hours", "cell-hours", "qualifying freezing-liquid cell-hours", "gust >= gust threshold"),
    Metric("1A Freezing liquid", "fr_high_pct", "High-wind share of freezing-liquid", "%", "qualifying freezing-liquid cell-hours", "high-wind / qualifying"),
    Metric("1A Freezing liquid", "fr_gust_max", "Maximum gust", "m/s", "qualifying freezing-liquid cell-hours", "maximum fg10"),
    Metric("1A Freezing liquid", "fr_temp_min", "Minimum temperature", "degC", "qualifying freezing-liquid cell-hours", "minimum T2m"),

    Metric("1B Wet snow", "wet_all", "Wet-snow ptype cell-hours, all temperatures", "cell-hours", "all DJF grid-cell-hours", "ptype = 6, before temperature filtering"),
    Metric("1B Wet snow", "wet", "Qualifying cold wet-snow cell-hours", "cell-hours", "all DJF grid-cell-hours", "ptype = 6 and T2m <= freezing threshold"),
    Metric("1B Wet snow", "wet_pct", "Qualifying wet-snow share", "%", "all DJF grid-cell-hours", "qualifying wet snow / all grid-cell-hours"),
    Metric("1B Wet snow", "wet_pct_ptype", "Cold share of wet-snow ptype", "%", "ptype 6 cell-hours", "qualifying / all ptype 6"),
    Metric("1B Wet snow", "wet_swe_mean", "Mean snowfall SWE rate", "mm/h", "qualifying wet-snow cell-hours", "mean avg_tsrwe"),
    Metric("1B Wet snow", "wet_swe_p95", "P95 snowfall SWE rate", "mm/h", "qualifying wet-snow cell-hours", "95th percentile avg_tsrwe"),
    Metric("1B Wet snow", "wet_swe_max", "Maximum snowfall SWE rate", "mm/h", "qualifying wet-snow cell-hours", "maximum avg_tsrwe"),
    Metric("1B Wet snow", "wet_precip_mean", "Mean precipitation rate", "mm/h", "qualifying wet-snow cell-hours", "mean avg_tprate"),
    Metric("1B Wet snow", "wet_high", "High-wind wet-snow cell-hours", "cell-hours", "qualifying wet-snow cell-hours", "gust >= gust threshold"),
    Metric("1B Wet snow", "wet_high_pct", "High-wind share of wet snow", "%", "qualifying wet-snow cell-hours", "high-wind / qualifying"),
    Metric("1B Wet snow", "wet_gust_max", "Maximum gust", "m/s", "qualifying wet-snow cell-hours", "maximum fg10"),

    Metric("2 In-cloud / rime potential", "cold", "Sub-zero cell-hours", "cell-hours", "all DJF grid-cell-hours", "T2m <= freezing threshold"),
    Metric("2 In-cloud / rime potential", "cold_pct", "Sub-zero share", "%", "all DJF grid-cell-hours", "sub-zero / all grid-cell-hours"),
    Metric("2 In-cloud / rime potential", "lcc_mean", "Mean low-cloud cover", "%", "sub-zero cell-hours", "mean LCC"),
    Metric("2 In-cloud / rime potential", "lcc_p75", "P75 low-cloud cover", "%", "sub-zero cell-hours", "75th percentile LCC"),
    Metric("2 In-cloud / rime potential", "lcc_p90", "P90 low-cloud cover", "%", "sub-zero cell-hours", "90th percentile LCC"),
    Metric("2 In-cloud / rime potential", "cbh_valid_pct", "Available cloud-base-height share", "%", "sub-zero cell-hours", "finite CBH / sub-zero cell-hours"),
    Metric("2 In-cloud / rime potential", "cbh_p50", "Median cloud-base height", "m", "sub-zero cell-hours with finite CBH", "50th percentile CBH"),
    Metric("2 In-cloud / rime potential", "cbh_p25", "P25 cloud-base height", "m", "sub-zero cell-hours with finite CBH", "25th percentile CBH"),
    Metric("2 In-cloud / rime potential", "cbh_p05", "P05 cloud-base height", "m", "sub-zero cell-hours with finite CBH", "5th percentile CBH"),
    Metric("2 In-cloud / rime potential", "tcslw_mean", "Mean total-column supercooled liquid water", "kg/m2", "sub-zero cell-hours", "mean TCSLW"),
    Metric("2 In-cloud / rime potential", "tcslw_p95", "P95 total-column supercooled liquid water", "kg/m2", "sub-zero cell-hours", "95th percentile TCSLW"),
    Metric("2 In-cloud / rime potential", "tcslw_p99", "P99 total-column supercooled liquid water", "kg/m2", "sub-zero cell-hours", "99th percentile TCSLW"),
    Metric("2 In-cloud / rime potential", "tcslw_max", "Maximum total-column supercooled liquid water", "kg/m2", "sub-zero cell-hours", "maximum TCSLW"),
    Metric("2 In-cloud / rime potential", "cold_dp_p50", "Median dewpoint depression", "degC", "sub-zero cell-hours", "median T2m - Td2m"),

    Metric("3 Cold moisture / snowfall", "temp_mean", "Mean temperature", "degC", "all DJF grid-cell-hours", "mean T2m"),
    Metric("3 Cold moisture / snowfall", "temp_p05", "P05 temperature", "degC", "all DJF grid-cell-hours", "5th percentile T2m"),
    Metric("3 Cold moisture / snowfall", "temp_min", "Minimum temperature", "degC", "all DJF grid-cell-hours", "minimum T2m"),
    Metric("3 Cold moisture / snowfall", "dp_p50", "Median dewpoint depression", "degC", "all DJF grid-cell-hours", "median T2m - Td2m"),
    Metric("3 Cold moisture / snowfall", "dp_p25", "P25 dewpoint depression", "degC", "all DJF grid-cell-hours", "25th percentile T2m - Td2m"),
    Metric("3 Cold moisture / snowfall", "dp_p05", "P05 dewpoint depression", "degC", "all DJF grid-cell-hours", "5th percentile T2m - Td2m"),
    Metric("3 Cold moisture / snowfall", "snowy", "Snowfall-positive cell-hours", "cell-hours", "all DJF grid-cell-hours", "avg_tsrwe > snowfall threshold"),
    Metric("3 Cold moisture / snowfall", "snowy_pct", "Snowfall-positive share", "%", "all DJF grid-cell-hours", "snowfall-positive / all grid-cell-hours"),
    Metric("3 Cold moisture / snowfall", "snowy_mean", "Mean snowfall SWE rate", "mm/h", "snowfall-positive cell-hours", "mean avg_tsrwe"),
    Metric("3 Cold moisture / snowfall", "snowy_p95", "P95 snowfall SWE rate", "mm/h", "snowfall-positive cell-hours", "95th percentile avg_tsrwe"),
    Metric("3 Cold moisture / snowfall", "snowy_max", "Maximum snowfall SWE rate", "mm/h", "snowfall-positive cell-hours", "maximum avg_tsrwe"),

    Metric("4 Cold high wind", "high", "High-wind cell-hours", "cell-hours", "all DJF grid-cell-hours", "fg10 >= gust threshold"),
    Metric("4 Cold high wind", "high_pct", "High-wind share", "%", "all DJF grid-cell-hours", "high-wind / all grid-cell-hours"),
    Metric("4 Cold high wind", "cold_high", "Sub-zero high-wind cell-hours", "cell-hours", "all DJF grid-cell-hours", "fg10 >= gust threshold and T2m <= freezing threshold"),
    Metric("4 Cold high wind", "cold_high_pct", "Sub-zero high-wind share", "%", "all DJF grid-cell-hours", "sub-zero high-wind / all grid-cell-hours"),
    Metric("4 Cold high wind", "cold_pct_high", "Sub-zero share of high-wind conditions", "%", "high-wind cell-hours", "sub-zero high-wind / all high-wind"),
    Metric("4 Cold high wind", "max_cold_gust", "Maximum gust while sub-zero", "m/s", "sub-zero cell-hours", "maximum fg10 where T2m <= freezing threshold"),
    Metric("4 Cold high wind", "temp_at_max_cold_gust", "Temperature at maximum sub-zero gust", "degC", "sub-zero cell-hour containing maximum gust", "T2m at maximum sub-zero fg10"),
)


def pct(a: int, b: int):
    return 100.0 * a / b if b else None


def process_region(config_path: Path, root: Path, freeze: float, gust_thr: float, snow_thr: float, start: int | None, end: int | None):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    name = cfg.get("display_name") or cfg["region"]
    y0 = int(cfg["years"]["start"])
    y1 = int(cfg["years"]["end"])
    if start is not None:
        y0 = max(y0, start)
    if end is not None:
        y1 = min(y1, end)
    if y1 < y0:
        raise ValueError(f"{name}: empty year range")

    a = Acc()
    for year in range(y0, y1 + 1):
        paths = validate_year_files(root / str(year), year)
        with h5py.File(paths["instant"], "r") as instant, h5py.File(paths["ptype"], "r") as pf, h5py.File(paths["avg"], "r") as avg, h5py.File(paths["max"], "r") as mx:
            t = kelvin_to_c(instant["t2m"][:])
            td = kelvin_to_c(instant["d2m"][:])
            tcslw = np.asarray(instant["tcslw"][:], dtype=np.float64)
            lcc = fraction_to_percent(instant["lcc"][:])
            cbh = np.asarray(instant["cbh"][:], dtype=np.float64)
            ptype = ptype_to_int(pf["ptype"][:])
            gust = np.asarray(mx["fg10"][:], dtype=np.float64)
            precip = rate_to_mmh(avg["avg_tprate"][:])
            snow = rate_to_mmh(avg["avg_tsrwe"][:])

        a.total += int(t.size)
        dp = t - td

        fr_ptype = np.isin(ptype, FREEZING_LIQUID_CODES)
        fr = fr_ptype & (t <= freeze)
        a.fr_ptype += int(np.count_nonzero(fr_ptype))
        a.fr += int(np.count_nonzero(fr))
        if np.any(fr):
            x = precip[fr]; a.fr_precip_s.add(x); a.fr_precip_q.add(x)
            x = gust[fr]; a.fr_gust_s.add(x); a.fr_high += int(np.count_nonzero(x >= gust_thr))
            a.fr_temp_s.add(t[fr])

        wet_all = ptype == WET_SNOW_CODE
        wet = wet_all & (t <= freeze)
        a.wet_all += int(np.count_nonzero(wet_all))
        a.wet += int(np.count_nonzero(wet))
        if np.any(wet):
            x = snow[wet]; a.wet_swe_s.add(x); a.wet_swe_q.add(x)
            a.wet_precip_s.add(precip[wet])
            x = gust[wet]; a.wet_gust_s.add(x); a.wet_high += int(np.count_nonzero(x >= gust_thr))

        cold = t <= freeze
        a.cold += int(np.count_nonzero(cold))
        if np.any(cold):
            x = lcc[cold]; a.cold_lcc_s.add(x); a.cold_lcc_q.add(x)
            x = cbh[cold]; x = x[np.isfinite(x)]; a.cold_cbh_valid += int(x.size); a.cold_cbh_q.add(x)
            x = tcslw[cold]; a.cold_tcslw_s.add(x); a.cold_tcslw_q.add(x)
            a.cold_dp_q.add(dp[cold])

        a.temp_s.add(t); a.temp_q.add(t); a.dp_q.add(dp)
        snowy = snow > snow_thr
        a.snowy += int(np.count_nonzero(snowy))
        if np.any(snowy):
            x = snow[snowy]; a.snowy_s.add(x); a.snowy_q.add(x)

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

        print(f"{name} {year}: processed {t.size:,} grid-cell-hours (running {a.total:,})")

    values = {
        "fr_ptype": a.fr_ptype, "fr": a.fr, "fr_pct": pct(a.fr, a.total), "fr_pct_ptype": pct(a.fr, a.fr_ptype),
        "fr_precip_mean": a.fr_precip_s.mean, "fr_precip_p95": a.fr_precip_q.p(95), "fr_precip_max": a.fr_precip_s.max,
        "fr_high": a.fr_high, "fr_high_pct": pct(a.fr_high, a.fr), "fr_gust_max": a.fr_gust_s.max, "fr_temp_min": a.fr_temp_s.min,
        "wet_all": a.wet_all, "wet": a.wet, "wet_pct": pct(a.wet, a.total), "wet_pct_ptype": pct(a.wet, a.wet_all),
        "wet_swe_mean": a.wet_swe_s.mean, "wet_swe_p95": a.wet_swe_q.p(95), "wet_swe_max": a.wet_swe_s.max,
        "wet_precip_mean": a.wet_precip_s.mean, "wet_high": a.wet_high, "wet_high_pct": pct(a.wet_high, a.wet), "wet_gust_max": a.wet_gust_s.max,
        "cold": a.cold, "cold_pct": pct(a.cold, a.total), "lcc_mean": a.cold_lcc_s.mean, "lcc_p75": a.cold_lcc_q.p(75), "lcc_p90": a.cold_lcc_q.p(90),
        "cbh_valid_pct": pct(a.cold_cbh_valid, a.cold), "cbh_p50": a.cold_cbh_q.p(50), "cbh_p25": a.cold_cbh_q.p(25), "cbh_p05": a.cold_cbh_q.p(5),
        "tcslw_mean": a.cold_tcslw_s.mean, "tcslw_p95": a.cold_tcslw_q.p(95), "tcslw_p99": a.cold_tcslw_q.p(99), "tcslw_max": a.cold_tcslw_s.max,
        "cold_dp_p50": a.cold_dp_q.p(50),
        "temp_mean": a.temp_s.mean, "temp_p05": a.temp_q.p(5), "temp_min": a.temp_s.min,
        "dp_p50": a.dp_q.p(50), "dp_p25": a.dp_q.p(25), "dp_p05": a.dp_q.p(5),
        "snowy": a.snowy, "snowy_pct": pct(a.snowy, a.total), "snowy_mean": a.snowy_s.mean, "snowy_p95": a.snowy_q.p(95), "snowy_max": a.snowy_s.max,
        "high": a.high, "high_pct": pct(a.high, a.total), "cold_high": a.cold_high, "cold_high_pct": pct(a.cold_high, a.total),
        "cold_pct_high": pct(a.cold_high, a.high), "max_cold_gust": a.max_cold_gust, "temp_at_max_cold_gust": a.temp_at_max_cold_gust,
    }
    meta = {"region": name, "config": str(config_path), "input_root": str(root), "years": {"start": y0, "end": y1}, "total_grid_cell_hours": a.total}
    return name, values, meta


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, (int, np.integer)):
        return int(v)
    return f"{float(v):.6f}"


def write_outputs(out: Path, results: dict, metadata: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    regions = list(results)
    with (out / "kpi_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["family", "metric_key", "metric", "unit", "denominator", "definition", *regions])
        for m in M:
            w.writerow([m.family, m.key, m.label, m.unit, m.denominator, m.definition, *[fmt(results[r].get(m.key)) for r in regions]])
    with (out / "kpi_long.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["region", "family", "metric_key", "metric", "value", "unit", "denominator", "definition"])
        for region in regions:
            for m in M:
                w.writerow([region, m.family, m.key, m.label, fmt(results[region].get(m.key)), m.unit, m.denominator, m.definition])
    (out / "kpi_run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"\nWrote {out / 'kpi_comparison.csv'}")
    print(f"Wrote {out / 'kpi_long.csv'}")
    print(f"Wrote {out / 'kpi_run_metadata.json'}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", action="append", nargs=2, metavar=("CONFIG", "INPUT_ROOT"), help="Repeatable dataset pair; defaults to project Montana + Larisa")
    p.add_argument("--output-dir", type=Path, default=Path("derived/kpis"))
    p.add_argument("--freezing-temp-c", type=float, default=0.0)
    p.add_argument("--gust-threshold-ms", type=float, default=18.0)
    p.add_argument("--snowfall-threshold-mmh", type=float, default=0.0)
    p.add_argument("--start-year", type=int)
    p.add_argument("--end-year", type=int)
    args = p.parse_args()

    datasets = args.dataset or [("config/montana.json", "data/raw/montana"), ("config/larisa.json", "data/raw/larisa")]
    results = {}
    region_meta = []
    for cfg, root in datasets:
        name, values, meta = process_region(Path(cfg), Path(root), args.freezing_temp_c, args.gust_threshold_ms, args.snowfall_threshold_mmh, args.start_year, args.end_year)
        if name in results:
            raise ValueError(f"Duplicate region name: {name}")
        results[name] = values
        region_meta.append(meta)

    metadata = {
        "method": "Direct year-by-year validated NetCDF + NumPy aggregation",
        "cell_hour_definition": "one ERA5 grid cell at one hourly timestamp",
        "thresholds": {
            "freezing_temp_c": args.freezing_temp_c,
            "gust_threshold_ms": args.gust_threshold_ms,
            "snowfall_threshold_mmh": args.snowfall_threshold_mmh,
            "freezing_liquid_ptype_codes": list(FREEZING_LIQUID_CODES),
            "wet_snow_ptype_code": WET_SNOW_CODE,
        },
        "percentiles": {"method": "numpy.percentile over all qualifying grid-cell-hours", "stored_quantile_dtype": "float32"},
        "regions": region_meta,
    }
    write_outputs(args.output_dir, results, metadata)


if __name__ == "__main__":
    main()
