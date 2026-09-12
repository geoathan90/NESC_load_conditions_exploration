INSERT INTO regions (name)
VALUES ('Montana');

INSERT INTO regions (name)
VALUES ('Larisa');

INSERT INTO precip_types (ptype_code, name) VALUES
    (0, 'No precipitation'),
    (1, 'Rain'),
    (2, 'Thunderstorm'),
    (3, 'Freezing rain'),
    (4, 'Mixed or ice'),
    (5, 'Snow'),
    (6, 'Wet snow'),
    (7, 'Rain and snow'),
    (8, 'Ice pellets'),
    (9, 'Graupel'),
    (10, 'Hail'),
    (11, 'Drizzle'),
    (12, 'Freezing drizzle'),
    (13, 'Hail < 5 mm'),
    (14, 'Hail >= 5 mm'),
    (255, 'Missing');

INSERT INTO times (time_utc)
VALUES ('1991-01-01T00:00:00Z');

INSERT INTO grid_cells (
    region_id,
    latitude,
    longitude
)
VALUES (
    2,
    40.25,
    21.75
);

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
)
VALUES (
    1,
    1,
    3,
    -2.4,
    -3.1,
    0.12,
    85.0,
    420.0,
    11.6,
    0.8,
    0.0
);