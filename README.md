# NESC load conditions exploration

Reproducible exploration of winter loading and icing-relevant meteorology for the Larisa study region, with the workflow designed for later reuse in Montana.

## Implemented pipeline

The repository now contains a complete configuration-driven pipeline that:

- recursively discovers and incrementally downloads public Google Drive year folders;
- strictly validates files, variables, units, step types, hourly timestamps, grids and cross-file alignment;
- merges instantaneous, time-mean and interval-maximum fields without interpolating categorical `ptype`;
- derives Celsius, dewpoint-depression, mm/h and percent variables while retaining the raw fields;
- produces occurrence, conditional-distribution, per-grid-cell and time-contiguous event tables;
- writes a period-specific Markdown numerical report and a Git-ignored derived NetCDF cache.

The numerical code is region-agnostic. Region bounds, Drive source, filenames,
variables, thresholds and storage locations live in YAML configuration.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/sync_drive_data.py --config config/larisa.yaml
.venv/bin/python scripts/run_weather_analysis.py --config config/larisa.yaml
.venv/bin/pytest -q
```

`NESC_DATA_ROOT` can override the configured local raw-data directory. The analysis
command discovers all complete local year directories by default; use
`--years 2013:2020` to select a period explicitly. Adding a new year folder to the
Drive root therefore requires no code change.

## Repository structure

```text
config/       Region and processing configuration
src/          Reusable processing code
scripts/      Command-line / orchestration entry points
notebooks/    Exploratory analysis only
manifests/    Machine-readable inventories of available source data
tests/        Validation and regression tests
docs/         Project notes and technical documentation
```

## Current Larisa source dataset and result

The initial weather archive is ECMWF ERA5 hourly data on single levels, downloaded from the Copernicus Climate Data Store in annual NetCDF4 packages for December, January and February. The regional bounds are:

- North: 40.25° N
- South: 39.25° N
- West: 21.75° E
- East: 22.75° E

The selected variables are 2 m temperature, 2 m dewpoint temperature, precipitation type, total-column supercooled liquid water, low cloud cover, cloud-base height, 10 m wind gust since previous post-processing, mean total precipitation rate, and mean snowfall rate.

The validated 2013–2020 run covers 17,328 timestamps on a 5 × 5 grid
(433,200 grid-cell-hours). See the primary report at
[`outputs/larisa/2013_2020/numerical_report.md`](outputs/larisa/2013_2020/numerical_report.md).

## Output contract

Each analysis period contains:

- `validation_manifest.csv`: source-file QA and coordinate/time inventory;
- `general_conditions.csv`: configured cold-temperature frequencies;
- `precipitation_type_occurrence.csv`: occurrence counts with explicit denominators;
- `conditional_statistics.csv`: tidy distributions for all winter, freezing liquid,
  wet snow and the combined accretion-relevant definition;
- `ptype_sensitivity.csv`: transparent trace-precipitation sensitivity cases;
- `ptype_diagnostics.csv`: rate/temperature combinations requiring careful interpretation;
- `event_extremes.csv`: individual grid-cell events using true hourly continuity;
- `per_grid_cell_summary.csv`: wide, QGIS-friendly cell metrics;
- `spatial_domain_summary.csv`: min/median/mean/max across cell-level metrics;
- `numerical_report.md`: concise table-led interpretation.

The combined derived NetCDF is placed under `derived/` and is not committed.

## Data-path principle

Raw NetCDF, derived NetCDF and GIS rasters are Git-ignored. Small manifests, tidy
CSV outputs and numerical reports are tracked for auditability. The current archive
is exploratory and must not be used by itself to claim NESC zone equivalence or
design adequacy.
