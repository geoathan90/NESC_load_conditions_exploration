import sqlite3
from pathlib import Path

from nesc_weather.database import PTYPE_LOOKUP, create_database, seed_precipitation_types


def test_schema_creation_and_lookup_seed(tmp_path: Path):
    schema = Path(__file__).resolve().parents[1] / "sql" / "0_schema.sql"
    db = tmp_path / "test.db"
    connection = create_database(db, schema)
    try:
        seed_precipitation_types(connection)
        connection.commit()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"regions", "grid_cells", "times", "precip_types", "weather_hourly"} <= tables
        assert connection.execute("SELECT COUNT(*) FROM precip_types").fetchone()[0] == len(PTYPE_LOOKUP)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()
