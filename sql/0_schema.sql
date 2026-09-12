PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE grid_cells (
    cell_id INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,

    UNIQUE (region_id, latitude, longitude),

    FOREIGN KEY (region_id)
        REFERENCES regions(region_id)
);

CREATE TABLE times (
    time_id INTEGER PRIMARY KEY,
    time_utc TEXT NOT NULL UNIQUE
);

CREATE TABLE precip_types (
    ptype_code INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE weather_hourly (
    cell_id INTEGER NOT NULL,
    time_id INTEGER NOT NULL,
    ptype_code INTEGER NOT NULL,

    t2m_c REAL NOT NULL,
    d2m_c REAL NOT NULL,

    tcslw_kg_m2 REAL NOT NULL,
    low_cloud_cover_pct REAL NOT NULL,
    cloud_base_height_m REAL,

    gust_10m_ms REAL NOT NULL,
    precip_rate_mmh REAL NOT NULL,
    snowfall_swe_rate_mmh REAL NOT NULL,

    PRIMARY KEY (cell_id, time_id),

    FOREIGN KEY (cell_id)
        REFERENCES grid_cells(cell_id),

    FOREIGN KEY (time_id)
        REFERENCES times(time_id),

    FOREIGN KEY (ptype_code)
        REFERENCES precip_types(ptype_code)
);

COMMIT;