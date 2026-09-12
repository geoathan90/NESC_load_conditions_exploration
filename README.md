# NESC Load Conditions Exploration

This repository builds a reproducible weather-analysis database from ERA5 single-level NetCDF files for Montana and Larisa.

The project is intentionally split into two layers:

1. **ETL / data preparation** — acquire raw files, validate them, normalize the ERA5 variables, and load a canonical SQLite database.
2. **Analysis** — query the SQLite database with transparent SQL for KPI and event-based comparisons.

Raw NetCDF files and generated SQLite databases are local/generated artifacts and are not committed to Git.

## Planned data flow

```text
Google Drive
    -> acquire
raw ERA5 NetCDF (instant / ptype / avg / max)
    -> validate
    -> transform
canonical 9-variable weather dataset
    -> SQLite
SQL exploration and KPI reporting
```

## Repository layout

```text
config/                 Region-specific configuration
src/nesc_weather/       Python ETL and validation package
scripts/                Command-line entry points
sql/                    Human-readable SQL analysis queries
tests/                  Automated tests
```
