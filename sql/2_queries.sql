.headers on
.mode column
.nullvalue NULL
-- .echo on
-- .bail on

-- sqlite3 local_data/nesc_weather.db < sql/2_queries.sql
-- sqlite3 local_data/nesc_weather.db < sql/2_queries.sql > output.txt

-- SELECT
--     SUM(t2m_c < -2) AS below_minus_2,
--     SUM(t2m_c >= -2 AND t2m_c < -1) AS minus_2_to_minus_1,
--     SUM(t2m_c >= -1 AND t2m_c <= 0) AS minus_1_to_0,
--     SUM(t2m_c > 0) AS above_0
-- FROM weather_hourly
-- WHERE ptype_code = 3;


-- SELECT
--     COUNT(*) AS n,
--     ROUND(MIN(precip_rate_mmh), 3) AS min_rate,
--     ROUND(AVG(precip_rate_mmh), 3) AS avg_rate,
--     ROUND(MAX(precip_rate_mmh), 3) AS max_rate
-- FROM weather_hourly
-- WHERE ptype_code = 3;


-- SELECT
--     SUM(precip_rate_mmh >= 0.1) AS over_0_1,
--     SUM(precip_rate_mmh >= 0.5) AS over_0_5,
--     SUM(precip_rate_mmh >= 1.0) AS over_1
-- FROM weather_hourly
-- WHERE ptype_code = 3;


-- SELECT
--     COUNT(*) AS n,
--     SUM(gust_10m_ms >= 10) AS gust_10_plus,
--     SUM(gust_10m_ms >= 15) AS gust_15_plus,
--     SUM(gust_10m_ms >= 18) AS gust_18_plus,
--     ROUND(MAX(gust_10m_ms), 2) AS max_gust
-- FROM weather_hourly
-- WHERE ptype_code = 3;


-- SELECT
--     p.name,
--     COUNT(*) AS cell_hours,
--     ROUND(MIN(w.t2m_c), 2) AS min_temp,
--     ROUND(AVG(w.t2m_c), 2) AS avg_temp,
--     ROUND(AVG(w.precip_rate_mmh), 3) AS avg_precip,
--     ROUND(MAX(w.gust_10m_ms), 2) AS max_gust
-- FROM weather_hourly w
-- JOIN precip_types p
--     ON w.ptype_code = p.ptype_code
-- GROUP BY w.ptype_code, p.name
-- ORDER BY cell_hours DESC;

SELECT
    g.latitude,
    g.longitude,
    COUNT(*) AS freezing_rain_cell_hours,
    ROUND(AVG(w.t2m_c), 2) AS avg_temp
FROM weather_hourly w
JOIN grid_cells g
    ON w.cell_id = g.cell_id
WHERE w.ptype_code = 3
GROUP BY g.cell_id
ORDER BY freezing_rain_cell_hours DESC;