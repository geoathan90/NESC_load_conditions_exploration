#!/usr/bin/env python3
"""Integrate Eugene ERA5 data into an existing nesc_weather.db.

Defaults:
    config/eugene.json
    data/raw/eugene/YYYY/
    local_data/nesc_weather.db

The database is never overwritten. Existing indexes are preserved and SQLite
updates them automatically as new rows are inserted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nesc_weather.database import connect, load_year  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("config/eugene.json"))
    p.add_argument("--input-root", type=Path, default=Path("data/raw/eugene"))
    p.add_argument("--db", type=Path, default=Path("local_data/nesc_weather.db"))
    p.add_argument("--start-year", type=int)
    p.add_argument("--end-year", type=int)
    args = p.parse_args()

    if not args.db.exists():
        raise FileNotFoundError(
            f"Existing database not found: {args.db}. "
            "This script intentionally does not create or overwrite a database."
        )

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    region_name = cfg.get("display_name") or cfg["region"]

    y0 = int(cfg["years"]["start"])
    y1 = int(cfg["years"]["end"])
    if args.start_year is not None:
        y0 = max(y0, args.start_year)
    if args.end_year is not None:
        y1 = min(y1, args.end_year)
    if y1 < y0:
        raise ValueError("Requested year range does not overlap the Eugene config.")

    con = connect(args.db)
    try:
        indexes_before = [
            row[1] for row in con.execute("PRAGMA index_list('weather_hourly')")
        ]
        print(f"Database: {args.db}")
        print(f"Loading {region_name}: {y0}-{y1}")
        print("Existing weather_hourly indexes:", ", ".join(indexes_before) or "(none)")

        loaded = 0
        for year in range(y0, y1 + 1):
            result = load_year(
                con,
                region_name=region_name,
                year=year,
                year_dir=args.input_root / str(year),
            )
            loaded += result["weather_rows"]
            print(
                f"{region_name} {year}: "
                f"{result['timestamps']} timestamps x "
                f"{result['grid_cells']} cells = "
                f"{result['weather_rows']:,} rows loaded"
            )

        summary = con.execute(
            """
            SELECT
                r.region_id,
                COUNT(DISTINCT gc.cell_id),
                COUNT(w.time_id)
            FROM regions AS r
            JOIN grid_cells AS gc ON gc.region_id = r.region_id
            LEFT JOIN weather_hourly AS w ON w.cell_id = gc.cell_id
            WHERE r.name = ?
            GROUP BY r.region_id
            """,
            (region_name,),
        ).fetchone()

        indexes_after = [
            row[1] for row in con.execute("PRAGMA index_list('weather_hourly')")
        ]

        print(f"Loaded this run: {loaded:,} rows")
        if summary:
            print(
                f"Eugene now has region_id={summary[0]}, "
                f"{summary[1]} grid cells, {summary[2]:,} weather rows"
            )
        print("Indexes after load:", ", ".join(indexes_after) or "(none)")
    finally:
        con.close()


if __name__ == "__main__":
    main()
