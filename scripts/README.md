# Scripts

From the repository root, after installing `requirements.txt`:

```bash
python scripts/sync_drive_data.py --config config/larisa.yaml
python scripts/run_weather_analysis.py --config config/larisa.yaml
```

The synchronizer recursively discovers year folders from the configured Drive root,
downloads only missing files, and writes `manifests/larisa_drive_inventory.csv`.
Use `--overwrite` only when an existing Drive file was replaced in place.

The analysis command discovers all locally available years by default. A bounded run
can be requested with `--years 2013:2020`. It validates before writing any analysis
outputs, creates period-specific CSV/report directories, and writes a Git-ignored
derived NetCDF cache containing both raw and analysis-friendly variables.
