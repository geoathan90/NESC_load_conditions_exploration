# Raster generation

This directory contains CLI tools that convert the project KPI calculations into QGIS-ready GeoTIFF rasters. Generated rasters are written under `raster_outputs/`, which is intentionally excluded from Git.

## Freezing-liquid rasters

`freezing_liquid_rasters.py` implements the existing **1A Freezing liquid** family spatially, one value per ERA5 grid cell. It uses the same headline classification as `scripts/calculate_kpis.py`:

- ERA5 precipitation type (`ptype`) is `3` or `12`;
- a cell-hour qualifies when `T2m <= 0 °C` by default;
- high wind means `fg10 >= 18 m/s` by default.

The thresholds are CLI options, so sensitivity runs do not require code changes.

The script does **not** write one raster per year. For annual-frequency metrics it calculates one 2-D array per year in memory and then reduces the year dimension to the requested climatological statistic. For conditional intensity metrics (precipitation rate, gust and temperature), it pools all qualifying cell-hours across the selected years and calculates the requested statistic per cell.

This deliberately follows the current KPI family's **cell-hour** semantics. It does not introduce a new definition of a multi-hour meteorological "event" or an event-gap rule.

All GeoTIFFs are written on the native ERA5 latitude/longitude grid in `EPSG:4326`. The script does not resample or interpolate the data. QGIS may render the grid smoothly, but the stored raster values retain the native ERA5 resolution.

## Installation

From the repository root:

```bash
pip install -r requirements.txt
```

`rasterio` is required for GeoTIFF output.

## Basic use

Generate the default raster suite for Larisa:

```bash
python raster_generation/freezing_liquid_rasters.py --region larisa
```

The region key resolves automatically to:

```text
config/<region>.json
data/raw/<region>/<year>/...
raster_outputs/<region>/freezing_liquid/...
```

For Larisa, the current config covers 1980-2025, so the default run uses all 46 years. The yearly NetCDF files must exist for the full selected range. Use `--start-year` and/or `--end-year` for a partial local dataset.

Examples:

```bash
# Only 2000-2025
python raster_generation/freezing_liquid_rasters.py \
  --region larisa \
  --start-year 2000

# Export only P95 and maximum rasters
python raster_generation/freezing_liquid_rasters.py \
  --region larisa \
  --stat p95 \
  --stat max

# Export only two metrics
python raster_generation/freezing_liquid_rasters.py \
  --region larisa \
  --metric fr_hours_per_year \
  --metric fr_precip_rate_mmh

# Sensitivity run with a different freezing threshold
python raster_generation/freezing_liquid_rasters.py \
  --region larisa \
  --freezing-temp-c -0.5
```

The `--metric` and `--stat` switches are repeatable. If omitted, all freezing-liquid raster metrics are generated with `mean`, `median`, `p95` and `max`.

Useful discovery commands:

```bash
python raster_generation/freezing_liquid_rasters.py --list-regions
python raster_generation/freezing_liquid_rasters.py --list-metrics
python raster_generation/freezing_liquid_rasters.py --help
```

A new region needs only the same input contract already used by the numerical pipeline: a `config/<region>.json` file and yearly data under `data/raw/<region>/`. The raster script itself does not require a region-specific code change. For example, once `config/eugene.json` exists and the Eugene download is complete, run:

```bash
python raster_generation/freezing_liquid_rasters.py --region eugene
```

For a nonstandard config or data location:

```bash
python raster_generation/freezing_liquid_rasters.py \
  --config config/custom_region.json \
  --input-root /path/to/yearly/netcdf
```

## Metrics and statistics

Annual metrics are summarized across calendar years (each year contains the project's January/February/December hours):

- `fr_ptype_hours_per_year`
- `fr_hours_per_year`
- `fr_share_pct`
- `fr_cold_share_ptype_pct`
- `fr_high_wind_hours_per_year`
- `fr_high_wind_share_pct`

Conditional metrics are summarized across all qualifying freezing-liquid cell-hours in the full selected period:

- `fr_precip_rate_mmh`
- `fr_gust_ms`
- `fr_temperature_c`

Available statistics are `mean`, `median`, `p05`, `p95`, `p99`, `min` and `max`. The default set is `mean`, `median`, `p95`, `max`.

For example:

```text
raster_outputs/larisa/freezing_liquid/fr_hours_per_year_mean.tif
raster_outputs/larisa/freezing_liquid/fr_hours_per_year_p95.tif
raster_outputs/larisa/freezing_liquid/fr_precip_rate_mmh_p95.tif
```

Each GeoTIFF also contains metadata tags describing the region, selected year range, thresholds, metric definition and aggregation semantics. A `metadata.json` file is written beside the rasters for the complete run configuration.

## Interpretation of P95

With 1980-2025 Larisa has 46 annual observations per cell. That is ample for descriptive mean/median mapping and gives a useful empirical annual P95, but the P95 raster should not be interpreted as a 50- or 100-year return-period design load. Return-period estimation is a separate extreme-value-analysis problem.
