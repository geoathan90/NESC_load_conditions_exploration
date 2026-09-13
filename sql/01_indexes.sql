-- sql/1_indexes.sql

CREATE INDEX IF NOT EXISTS idx_weather_wetsnow_rate
ON weather_hourly (
    snowfall_swe_rate_mmh,
    cell_id,
    time_id
)
WHERE ptype_code = 6;