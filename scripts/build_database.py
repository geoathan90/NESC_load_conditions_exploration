"""Build or extend the SQLite ERA5 weather database from one or more local year folders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nesc_weather.database import create_database, load_year  # noqa: E402


def parse_years(value: str) -> list[int]:
    if ":" in value:
        start_text, end_text = value.split(":", 1)
        start, end = int(start_text), int(end_text)
        if end < start:
            raise argparse.ArgumentTypeError("year range end must be >= start")
        return list(range(start, end + 1))
    return [int(value)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Region JSON config")
    parser.add_argument("--input-root", type=Path, required=True, help="Region raw-data root containing YEAR/ folders")
    parser.add_argument("--db", type=Path, default=Path("local_data/nesc_weather.db"))
    parser.add_argument("--schema", type=Path, default=Path("sql/0_schema.sql"))
    parser.add_argument("--years", type=parse_years, required=True, help="Single year or inclusive range, e.g. 1991 or 1991:2020")
    parser.add_argument("--overwrite", action="store_true", help="Delete and recreate the database before loading")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    region_name = config.get("display_name") or config["region"]

    connection = create_database(args.db, args.schema, overwrite=args.overwrite)
    try:
        for year in args.years:
            year_dir = args.input_root / str(year)
            result = load_year(
                connection,
                region_name=region_name,
                year=year,
                year_dir=year_dir,
            )
            print(
                f"{region_name} {year}: {result['timestamps']} timestamps × "
                f"{result['grid_cells']} cells = {result['weather_rows']} rows loaded"
            )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
