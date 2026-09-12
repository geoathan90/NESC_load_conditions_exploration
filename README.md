# NESC Load Conditions Exploration

This repository builds a reproducible weather-analysis database from ERA5 single-level NetCDF files for Montana and Larisa.

The project is intentionally split into two layers:

1. **ETL / data preparation** — acquire raw files, validate them, normalize the ERA5 variables, and load a canonical SQLite database.
2. **Analysis** — query the SQLite database with transparent SQL for KPI and event-based comparisons.

Raw NetCDF files and generated SQLite databases are local/generated artifacts and are not committed to Git.

## Data flow

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
sql/                    Schema and human-readable SQL analysis queries
tests/                  Automated tests
```

## Raw yearly input contract

Each year folder must contain exactly the canonical four-file layout used for both regions:

```text
YEAR/
  data_stream-oper_stepType-instant.nc
  data_stream-oper_stepType-ptype.nc
  data_stream-oper_stepType-avg.nc
  data_stream-oper_stepType-max.nc
```

The loader validates the expected variables, GRIB step types and units; the Jan/Feb/Dec hourly timestamp sequence; and exact cross-file grid/time alignment. Longitudes are normalized to `[-180, 180)` before alignment so the Montana ptype 0-360 convention is handled without altering the raw files.

## Canonical transformations

```text
t2m, d2m          K -> degC
lcc               0..1 -> percent
avg_tprate        kg m^-2 s^-1 -> mm/h
avg_tsrwe         kg m^-2 s^-1 -> mm SWE/h
ptype             integer code retained
```

`tcslw`, `cbh` and `fg10` retain their source units. `cbh` may be NULL; the other canonical weather fields are required to be finite.

## First real ETL test: Larisa 1991

Install dependencies, place the four 1991 files under `data/raw/larisa/1991/`, then run:

```bash
python scripts/build_database.py \
  --config config/larisa.json \
  --input-root data/raw/larisa \
  --db local_data/nesc_weather.db \
  --schema sql/0_schema.sql \
  --years 1991 \
  --overwrite
```

The expected Larisa 1991 load is:

```text
2160 timestamps x 25 cells = 54000 weather rows
```

Verify the resulting database with:

```bash
python scripts/verify_database.py --db local_data/nesc_weather.db
```

To download a single shared Google Drive year folder with `gdown`:

```bash
python scripts/download_drive_year.py \
  --url "<GOOGLE_DRIVE_YEAR_FOLDER_URL>" \
  --output data/raw/larisa/1991
```

## Multi-year loading

After a successful one-year test, additional years can be loaded into the same database:

```bash
python scripts/build_database.py \
  --config config/larisa.json \
  --input-root data/raw/larisa \
  --db local_data/nesc_weather.db \
  --schema sql/0_schema.sql \
  --years 1992:2020
```

Each year is loaded in one SQLite transaction. A duplicate cell/time observation is rejected by the schema rather than silently overwritten.
