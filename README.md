# NESC load conditions exploration

Reproducible exploration of winter loading and icing-relevant meteorology for the Larisa study region, with the workflow designed for later reuse in Montana.

## Repository role

This repository stores **code, configuration, manifests, notebooks, tests, and documentation**. Large raw meteorological and terrain datasets should live outside Git, e.g. in Google Drive, and be referenced through a configurable data-root path.

## Planned structure

```text
config/       Region and processing configuration
src/          Reusable processing code
scripts/      Command-line / orchestration entry points
notebooks/    Exploratory analysis only
manifests/    Machine-readable inventories of available source data
tests/        Validation and regression tests
docs/         Project notes and technical documentation
```

## Current Larisa source dataset

The initial weather archive is ECMWF ERA5 hourly data on single levels, downloaded from the Copernicus Climate Data Store in annual NetCDF4 packages for December, January and February. The regional bounds are:

- North: 40.25° N
- South: 39.25° N
- West: 21.75° E
- East: 22.75° E

The selected variables are 2 m temperature, 2 m dewpoint temperature, precipitation type, total-column supercooled liquid water, low cloud cover, cloud-base height, 10 m wind gust since previous post-processing, mean total precipitation rate, and mean snowfall rate.

## Data-path principle

Processing code must not assume that raw data are stored inside the repository. A configurable environment variable such as `NESC_DATA_ROOT` will point to the external data archive.
