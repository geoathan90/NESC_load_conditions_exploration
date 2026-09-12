"""Print compact integrity/count checks for the SQLite weather database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def scalar(connection: sqlite3.Connection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("local_data/nesc_weather.db"))
    args = parser.parse_args()

    connection = sqlite3.connect(args.db)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        print(f"regions:        {scalar(connection, 'SELECT COUNT(*) FROM regions')}")
        print(f"grid_cells:     {scalar(connection, 'SELECT COUNT(*) FROM grid_cells')}")
        print(f"times:          {scalar(connection, 'SELECT COUNT(*) FROM times')}")
        print(f"precip_types:   {scalar(connection, 'SELECT COUNT(*) FROM precip_types')}")
        print(f"weather_hourly: {scalar(connection, 'SELECT COUNT(*) FROM weather_hourly')}")
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        print(f"foreign_key_check: {'PASS' if not violations else 'FAIL'}")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"integrity_check:   {integrity}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
