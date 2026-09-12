"""SQLite loading helpers for canonical ERA5 weather observations."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np

from .transform import (
    epoch_seconds_to_iso_z,
    fraction_to_percent,
    kelvin_to_c,
    ptype_to_int,
    rate_to_mmh,
    require_finite,
)
from .validation import normalize_longitudes, validate_year_files

PTYPE_LOOKUP = [
    (0, "No precipitation"),
    (1, "Rain"),
    (2, "Thunderstorm"),
    (3, "Freezing rain"),
    (4, "Mixed or ice"),
    (5, "Snow"),
    (6, "Wet snow"),
    (7, "Rain and snow"),
    (8, "Ice pellets"),
    (9, "Graupel"),
    (10, "Hail"),
    (11, "Drizzle"),
    (12, "Freezing drizzle"),
    (13, "Hail < 5 mm"),
    (14, "Hail >= 5 mm"),
    (255, "Missing"),
]

WEATHER_INSERT_SQL = """
INSERT INTO weather_hourly (
    cell_id,
    time_id,
    ptype_code,
    t2m_c,
    d2m_c,
    tcslw_kg_m2,
    low_cloud_cover_pct,
    cloud_base_height_m,
    gust_10m_ms,
    precip_rate_mmh,
    snowfall_swe_rate_mmh
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_database(db_path: Path, schema_path: Path, overwrite: bool = False) -> sqlite3.Connection:
    db_path = Path(db_path)
    schema_path = Path(schema_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite and db_path.exists():
        db_path.unlink()
    if not db_path.exists():
        connection = connect(db_path)
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        return connection
    return connect(db_path)


def seed_precipitation_types(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT OR IGNORE INTO precip_types (ptype_code, name) VALUES (?, ?)",
        PTYPE_LOOKUP,
    )


def _get_or_create_region(connection: sqlite3.Connection, region_name: str) -> int:
    connection.execute("INSERT OR IGNORE INTO regions (name) VALUES (?)", (region_name,))
    row = connection.execute(
        "SELECT region_id FROM regions WHERE name = ?", (region_name,)
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Could not resolve region_id for {region_name!r}")
    return int(row[0])


def _insert_grid_cells(
    connection: sqlite3.Connection,
    region_id: int,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
) -> np.ndarray:
    pairs = [(float(lat), float(lon)) for lat in latitudes for lon in longitudes]
    connection.executemany(
        "INSERT OR IGNORE INTO grid_cells (region_id, latitude, longitude) VALUES (?, ?, ?)",
        ((region_id, lat, lon) for lat, lon in pairs),
    )
    rows = connection.execute(
        "SELECT cell_id, latitude, longitude FROM grid_cells WHERE region_id = ?",
        (region_id,),
    ).fetchall()
    mapping = {(round(float(lat), 10), round(float(lon), 10)): int(cell_id) for cell_id, lat, lon in rows}
    try:
        return np.asarray(
            [mapping[(round(lat, 10), round(lon, 10))] for lat, lon in pairs],
            dtype=np.int64,
        )
    except KeyError as exc:
        raise RuntimeError(f"Could not resolve cell_id for coordinate {exc.args[0]}") from exc


def _insert_times(connection: sqlite3.Connection, time_strings: list[str]) -> np.ndarray:
    connection.executemany(
        "INSERT OR IGNORE INTO times (time_utc) VALUES (?)",
        ((value,) for value in time_strings),
    )
    mapping = {value: int(time_id) for time_id, value in connection.execute("SELECT time_id, time_utc FROM times")}
    return np.asarray([mapping[value] for value in time_strings], dtype=np.int64)


def _none_if_nan(value: float) -> float | None:
    value = float(value)
    return None if np.isnan(value) else value


def load_year(
    connection: sqlite3.Connection,
    *,
    region_name: str,
    year: int,
    year_dir: Path,
    batch_hours: int = 48,
) -> dict[str, int]:
    """Validate, transform and load one region-year atomically."""
    paths = validate_year_files(Path(year_dir), year)

    with h5py.File(paths["instant"], "r") as instant, h5py.File(
        paths["ptype"], "r"
    ) as ptype_file, h5py.File(paths["avg"], "r") as avg, h5py.File(paths["max"], "r") as max_file:
        epoch_seconds = np.asarray(instant["valid_time"][:], dtype=np.int64)
        latitudes = np.asarray(instant["latitude"][:], dtype=np.float64)
        longitudes = normalize_longitudes(instant["longitude"][:])

        t2m_c = kelvin_to_c(instant["t2m"][:])
        d2m_c = kelvin_to_c(instant["d2m"][:])
        tcslw = np.asarray(instant["tcslw"][:], dtype=np.float64)
        lcc_pct = fraction_to_percent(instant["lcc"][:])
        cbh = np.asarray(instant["cbh"][:], dtype=np.float64)
        ptype = ptype_to_int(ptype_file["ptype"][:])
        gust = np.asarray(max_file["fg10"][:], dtype=np.float64)
        precip = rate_to_mmh(avg["avg_tprate"][:])
        snowfall = rate_to_mmh(avg["avg_tsrwe"][:])

    for name, values in (
        ("t2m_c", t2m_c),
        ("d2m_c", d2m_c),
        ("tcslw_kg_m2", tcslw),
        ("low_cloud_cover_pct", lcc_pct),
        ("gust_10m_ms", gust),
        ("precip_rate_mmh", precip),
        ("snowfall_swe_rate_mmh", snowfall),
    ):
        require_finite(name, values)

    time_strings = epoch_seconds_to_iso_z(epoch_seconds)
    ny = len(latitudes)
    nx = len(longitudes)
    cells_per_hour = ny * nx

    try:
        connection.execute("BEGIN")
        seed_precipitation_types(connection)
        region_id = _get_or_create_region(connection, region_name)
        cell_ids = _insert_grid_cells(connection, region_id, latitudes, longitudes)
        time_ids = _insert_times(connection, time_strings)

        inserted = 0
        for start in range(0, len(time_ids), batch_hours):
            stop = min(start + batch_hours, len(time_ids))
            rows: list[tuple[object, ...]] = []
            for ti in range(start, stop):
                flat_t2m = t2m_c[ti].reshape(-1)
                flat_d2m = d2m_c[ti].reshape(-1)
                flat_tcslw = tcslw[ti].reshape(-1)
                flat_lcc = lcc_pct[ti].reshape(-1)
                flat_cbh = cbh[ti].reshape(-1)
                flat_ptype = ptype[ti].reshape(-1)
                flat_gust = gust[ti].reshape(-1)
                flat_precip = precip[ti].reshape(-1)
                flat_snow = snowfall[ti].reshape(-1)

                for ci in range(cells_per_hour):
                    rows.append(
                        (
                            int(cell_ids[ci]),
                            int(time_ids[ti]),
                            int(flat_ptype[ci]),
                            float(flat_t2m[ci]),
                            float(flat_d2m[ci]),
                            float(flat_tcslw[ci]),
                            float(flat_lcc[ci]),
                            _none_if_nan(flat_cbh[ci]),
                            float(flat_gust[ci]),
                            float(flat_precip[ci]),
                            float(flat_snow[ci]),
                        )
                    )
            connection.executemany(WEATHER_INSERT_SQL, rows)
            inserted += len(rows)

        connection.commit()
    except Exception:
        connection.rollback()
        raise

    expected_rows = len(time_ids) * cells_per_hour
    if inserted != expected_rows:
        raise RuntimeError(f"Inserted {inserted} rows, expected {expected_rows}")

    return {
        "region_id": region_id,
        "timestamps": len(time_ids),
        "grid_cells": cells_per_hour,
        "weather_rows": inserted,
    }
