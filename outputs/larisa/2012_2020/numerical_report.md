# Larisa ERA5 winter numerical exploration (2012–2020)

## Scope

This is the first repeatable numerical exploration of the available January, February and December observations. The eight-year archive is suitable for pipeline development and exploratory comparison, but not for a final NESC loading-zone classification, design adequacy conclusion, or climatological equivalence claim.

All percentages labelled **all hours** use valid grid-cell-hours as the denominator. Percentages labelled **ptype precipitation** use valid observations with ECMWF `ptype != 0` as the denominator. No spatial averaging is performed before the per-cell metrics are calculated.

## A. Dataset QA

| Item | Result |
| --- | --- |
| Years | 2012–2020 (9 years) |
| Selected months | 1, 2, 12 |
| Unique timestamps | 19,512 |
| Grid | 5 latitude × 5 longitude |
| Grid-cell-hours | 487,800 |
| Latitude coordinates | 40.25, 40, 39.75, 39.5, 39.25 |
| Longitude coordinates | 21.75, 22, 22.25, 22.5, 22.75 |
| Validated source files | 27/27 |
| Unexpected within-month hourly gaps | 0 |

Annual time coverage is checked against every expected hour in each selected calendar month; the March–November interval is intentionally absent.

| Year | Timestamps | Observed hourly segments | Coverage valid |
| --- | --- | --- | --- |
| 2012 | 2,184 | 2012-01-01T00:00:00 → 2012-02-29T23:00:00; 2012-12-01T00:00:00 → 2012-12-31T23:00:00 | yes |
| 2013 | 2,160 | 2013-01-01T00:00:00 → 2013-02-28T23:00:00; 2013-12-01T00:00:00 → 2013-12-31T23:00:00 | yes |
| 2014 | 2,160 | 2014-01-01T00:00:00 → 2014-02-28T23:00:00; 2014-12-01T00:00:00 → 2014-12-31T23:00:00 | yes |
| 2015 | 2,160 | 2015-01-01T00:00:00 → 2015-02-28T23:00:00; 2015-12-01T00:00:00 → 2015-12-31T23:00:00 | yes |
| 2016 | 2,184 | 2016-01-01T00:00:00 → 2016-02-29T23:00:00; 2016-12-01T00:00:00 → 2016-12-31T23:00:00 | yes |
| 2017 | 2,160 | 2017-01-01T00:00:00 → 2017-02-28T23:00:00; 2017-12-01T00:00:00 → 2017-12-31T23:00:00 | yes |
| 2018 | 2,160 | 2018-01-01T00:00:00 → 2018-02-28T23:00:00; 2018-12-01T00:00:00 → 2018-12-31T23:00:00 | yes |
| 2019 | 2,160 | 2019-01-01T00:00:00 → 2019-02-28T23:00:00; 2019-12-01T00:00:00 → 2019-12-31T23:00:00 | yes |
| 2020 | 2,184 | 2020-01-01T00:00:00 → 2020-02-29T23:00:00; 2020-12-01T00:00:00 → 2020-12-31T23:00:00 | yes |

Missing values are counted across the full time × latitude × longitude population.

| Variable | Missing grid-cell-hours | Missing (%) |
| --- | --- | --- |
| t2m | 0 | 0.000 |
| d2m | 0 | 0.000 |
| ptype | 0 | 0.000 |
| tcslw | 0 | 0.000 |
| lcc | 0 | 0.000 |
| cbh | 119,051 | 24.406 |
| fg10 | 0 | 0.000 |
| avg_tprate | 0 | 0.000 |
| avg_tsrwe | 0 | 0.000 |
| t2m_c | 0 | 0.000 |
| d2m_c | 0 | 0.000 |
| dewpoint_depression_c | 0 | 0.000 |
| precip_rate_mmh | 0 | 0.000 |
| snowfall_rate_mmh | 0 | 0.000 |
| low_cloud_cover_pct | 0 | 0.000 |

Validation result: all required files, variables, timestamps and grids aligned exactly across instant/avg/max packages and across years.

## B. General winter conditions

| Temperature frequency | Grid-cell-hours | Percent |
| --- | --- | --- |
| t2m_at_or_below_0_c | 58,459 | 11.984 |
| t2m_at_or_below_-5_c | 7,204 | 1.477 |
| t2m_at_or_below_-10_c | 745 | 0.153 |

| Variable | Units | Valid | Missing | Mean | Median | P95 | P99 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| t2m_c | degC | 487,800 | 0 | 6.128 | 6.395 | 13.850 | 16.801 | 24.878 |
| dewpoint_depression_c | degC | 487,800 | 0 | 4.528 | 3.564 | 11.622 | 15.276 | 33.693 |
| precip_rate_mmh | mm h-1 | 487,800 | 0 | 0.121 | 0.000 | 0.707 | 1.949 | 8.659 |
| snowfall_rate_mmh | mm h-1 water equivalent | 487,800 | 0 | 0.021 | 0.000 | 0.063 | 0.577 | 5.478 |
| fg10 | m s-1 | 487,800 | 0 | 5.417 | 4.690 | 11.203 | 15.292 | 33.527 |
| low_cloud_cover_pct | percent | 487,800 | 0 | 34.670 | 15.640 | 100.000 | 100.000 | 100.000 |
| tcslw | kg m-2 | 487,800 | 0 | 0.036 | 0.002 | 0.197 | 0.355 | 1.370 |
| cbh | m | 368,749 | 119,051 | 1,232.856 | 563.227 | 5,841.229 | 8,420.781 | 14,010.276 |

## C. Precipitation-type occurrence

| Category | Code(s) | Count | % all hours | Count in ptype precip | % ptype precip |
| --- | --- | --- | --- | --- | --- |
| freezing_rain | 3 | 1,030 | 0.211 | 1,030 | 0.449 |
| freezing_drizzle | 12 | 0 | 0.000 | 0 | 0.000 |
| freezing_liquid | 3;12 | 1,030 | 0.211 | 1,030 | 0.449 |
| wet_snow | 6 | 12,198 | 2.501 | 12,198 | 5.316 |
| accretion_relevant | 3;6;12 | 13,228 | 2.712 | 13,228 | 5.765 |
| rain | 1 | 184,692 | 37.862 | 184,692 | 80.497 |
| ordinary_snow | 5 | 23,999 | 4.920 | 23,999 | 10.460 |
| rain_and_snow | 7 | 4,054 | 0.831 | 4,054 | 1.767 |
| ice_pellets | 8 | 3,468 | 0.711 | 3,468 | 1.511 |
| thunderstorm | 2 | 0 | 0.000 | 0 | 0.000 |
| no_precipitation | 0 | 258,359 | 52.964 | 0 | 0.000 |

`freezing_liquid` is codes 3 or 12. `accretion_relevant` is codes 3, 6 or 12. Ordinary snow and ice pellets are not included in that combined category.

### Trace-precipitation sensitivity

The unfiltered ptype classification remains the primary definition. The table below shows the effect of illustrative mean-rate filters; none is adopted as a final scientific threshold.

| Minimum precip rate (mm/h) | Retained count | % retained | % all hours |
| --- | --- | --- | --- |
| 0.000 | 13,228 | 100.000 | 2.712 |
| 0.010 | 9,078 | 68.627 | 1.861 |
| 0.100 | 5,542 | 41.896 | 1.136 |

### Diagnostic combinations requiring cautious interpretation

| Category | Diagnostic | Count | Category total | Percent |
| --- | --- | --- | --- | --- |
| freezing_liquid | zero_interval_mean_precip_rate | 112 | 1,030 | 10.874 |
| freezing_liquid | precip_rate_below_0.01_mmh | 606 | 1,030 | 58.835 |
| freezing_liquid | t2m_above_0_c | 560 | 1,030 | 54.369 |
| freezing_liquid | t2m_above_2_c | 48 | 1,030 | 4.660 |
| wet_snow | zero_interval_mean_precip_rate | 1,154 | 12,198 | 9.461 |
| wet_snow | precip_rate_below_0.01_mmh | 3,544 | 12,198 | 29.054 |
| wet_snow | t2m_above_5_c | 187 | 12,198 | 1.533 |

These combinations are not automatically errors: ptype is derived from the model's vertical thermodynamic structure, while `t2m` is only the 2 m air temperature and the rate is an interval mean. They do make an unfiltered ptype count a poor proxy for verified surface accretion.

## D. Conditional icing-relevant statistics

| Condition | Variable | Units | Valid | Missing | Mean | Median | P95 | P99 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_winter | t2m_c | degC | 487,800 | 0 | 6.128 | 6.395 | 13.850 | 16.801 | 24.878 |
| all_winter | dewpoint_depression_c | degC | 487,800 | 0 | 4.528 | 3.564 | 11.622 | 15.276 | 33.693 |
| all_winter | precip_rate_mmh | mm h-1 | 487,800 | 0 | 0.121 | 0.000 | 0.707 | 1.949 | 8.659 |
| all_winter | snowfall_rate_mmh | mm h-1 water equivalent | 487,800 | 0 | 0.021 | 0.000 | 0.063 | 0.577 | 5.478 |
| all_winter | fg10 | m s-1 | 487,800 | 0 | 5.417 | 4.690 | 11.203 | 15.292 | 33.527 |
| all_winter | low_cloud_cover_pct | percent | 487,800 | 0 | 34.670 | 15.640 | 100.000 | 100.000 | 100.000 |
| all_winter | tcslw | kg m-2 | 487,800 | 0 | 0.036 | 0.002 | 0.197 | 0.355 | 1.370 |
| all_winter | cbh | m | 368,749 | 119,051 | 1,232.856 | 563.227 | 5,841.229 | 8,420.781 | 14,010.276 |
| freezing_liquid | t2m_c | degC | 1,030 | 0 | 0.046 | 0.163 | 1.974 | 2.515 | 2.944 |
| freezing_liquid | dewpoint_depression_c | degC | 1,030 | 0 | 1.009 | 0.762 | 2.658 | 3.631 | 5.949 |
| freezing_liquid | precip_rate_mmh | mm h-1 | 1,030 | 0 | 0.053 | 0.005 | 0.261 | 1.117 | 2.062 |
| freezing_liquid | snowfall_rate_mmh | mm h-1 water equivalent | 1,030 | 0 | 0.005 | 0.000 | 0.007 | 0.106 | 0.719 |
| freezing_liquid | fg10 | m s-1 | 1,030 | 0 | 4.225 | 3.784 | 7.809 | 10.338 | 17.492 |
| freezing_liquid | low_cloud_cover_pct | percent | 1,030 | 0 | 63.333 | 71.764 | 100.000 | 100.000 | 100.000 |
| freezing_liquid | tcslw | kg m-2 | 1,030 | 0 | 0.036 | 0.020 | 0.130 | 0.222 | 0.369 |
| freezing_liquid | cbh | m | 1,000 | 30 | 411.067 | 140.498 | 1,711.798 | 3,109.655 | 7,365.747 |
| wet_snow | t2m_c | degC | 12,198 | 0 | 1.953 | 2.025 | 4.149 | 5.307 | 7.750 |
| wet_snow | dewpoint_depression_c | degC | 12,198 | 0 | 4.866 | 4.348 | 11.092 | 13.732 | 16.791 |
| wet_snow | precip_rate_mmh | mm h-1 | 12,198 | 0 | 0.296 | 0.070 | 1.357 | 2.742 | 5.714 |
| wet_snow | snowfall_rate_mmh | mm h-1 water equivalent | 12,198 | 0 | 0.257 | 0.059 | 1.181 | 2.404 | 5.478 |
| wet_snow | fg10 | m s-1 | 12,198 | 0 | 7.367 | 6.735 | 13.999 | 16.827 | 27.692 |
| wet_snow | low_cloud_cover_pct | percent | 12,198 | 0 | 66.613 | 81.149 | 100.000 | 100.000 | 100.000 |
| wet_snow | tcslw | kg m-2 | 12,198 | 0 | 0.086 | 0.057 | 0.265 | 0.423 | 1.104 |
| wet_snow | cbh | m | 12,075 | 123 | 713.552 | 607.357 | 1,801.903 | 2,860.532 | 6,284.604 |
| accretion_relevant | t2m_c | degC | 13,228 | 0 | 1.805 | 1.910 | 4.101 | 5.260 | 7.750 |
| accretion_relevant | dewpoint_depression_c | degC | 13,228 | 0 | 4.566 | 3.999 | 10.954 | 13.666 | 16.791 |
| accretion_relevant | precip_rate_mmh | mm h-1 | 13,228 | 0 | 0.277 | 0.057 | 1.316 | 2.615 | 5.714 |
| accretion_relevant | snowfall_rate_mmh | mm h-1 water equivalent | 13,228 | 0 | 0.237 | 0.042 | 1.135 | 2.332 | 5.478 |
| accretion_relevant | fg10 | m s-1 | 13,228 | 0 | 7.123 | 6.428 | 13.823 | 16.660 | 27.692 |
| accretion_relevant | low_cloud_cover_pct | percent | 13,228 | 0 | 66.358 | 80.595 | 100.000 | 100.000 | 100.000 |
| accretion_relevant | tcslw | kg m-2 | 13,228 | 0 | 0.082 | 0.052 | 0.262 | 0.415 | 1.104 |
| accretion_relevant | cbh | m | 13,075 | 153 | 690.418 | 574.629 | 1,795.631 | 2,882.492 | 7,365.747 |

## E. Spatial statistics

Each metric is first computed independently at each grid cell. The following summarizes those 25 cell-level results across the domain.

| Per-cell metric | Cells | Minimum | Median | Mean | Maximum |
| --- | --- | --- | --- | --- | --- |
| t2m_c_mean | 25 | 3.157 | 6.272 | 6.128 | 9.915 |
| t2m_at_or_below_0_c_pct | 25 | 0.436 | 12.567 | 11.984 | 25.671 |
| t2m_at_or_below_minus_5_c_pct | 25 | 0.000 | 1.158 | 1.477 | 4.203 |
| t2m_at_or_below_minus_10_c_pct | 25 | 0.000 | 0.056 | 0.153 | 0.723 |
| fg10_p95 | 25 | 7.707 | 10.709 | 10.721 | 14.514 |
| fg10_max | 25 | 19.191 | 25.367 | 25.479 | 33.527 |
| precip_rate_mmh_mean | 25 | 0.086 | 0.121 | 0.121 | 0.181 |
| precip_rate_mmh_max | 25 | 4.056 | 5.825 | 6.060 | 8.659 |
| tcslw_mean | 25 | 0.026 | 0.036 | 0.036 | 0.043 |
| tcslw_max | 25 | 0.519 | 0.894 | 0.935 | 1.370 |
| freezing_liquid_pct_all_hours | 25 | 0.000 | 0.133 | 0.211 | 0.958 |
| wet_snow_pct_all_hours | 25 | 1.394 | 2.276 | 2.501 | 4.382 |
| accretion_relevant_pct_all_hours | 25 | 1.527 | 2.368 | 2.712 | 4.766 |
| event_count | 25 | 43.000 | 125.000 | 133.400 | 290.000 |
| maximum_event_duration_hours | 25 | 16.000 | 23.000 | 30.360 | 66.000 |

## F. Event and extreme exploration

Detected **3,335** individual grid-cell events, of which **2,225** lasted at least two consecutive hours. Events break whenever the next actual timestamp is not exactly one hour later, so the March–November archive gap cannot join two episodes.

| Cell | Start | Hours | ptype | T mean °C | Gust max m/s | Precip mm | Snowfall mm w.e. | TCSLW max kg/m² |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40.25, 22.75 | 2012-02-07T00:00:00 | 66 | wet_snow | 2.338 | 22.844 | 30.057 | 21.880 | 0.838 |
| 40.25, 22.50 | 2012-02-07T00:00:00 | 66 | wet_snow | -0.077 | 19.898 | 32.252 | 31.516 | 0.595 |
| 40.00, 22.75 | 2014-12-30T02:00:00 | 50 | wet_snow | 1.761 | 16.827 | 11.916 | 11.590 | 0.148 |
| 40.00, 22.50 | 2014-12-30T02:00:00 | 50 | wet_snow | -1.489 | 14.563 | 10.731 | 10.732 | 0.106 |
| 39.75, 21.75 | 2017-12-20T15:00:00 | 47 | wet_snow | 1.241 | 5.456 | 8.371 | 7.990 | 0.344 |
| 40.25, 22.75 | 2014-12-30T05:00:00 | 45 | wet_snow | 1.896 | 14.508 | 4.975 | 4.793 | 0.124 |
| 40.25, 22.50 | 2014-12-30T05:00:00 | 45 | wet_snow | -1.260 | 12.359 | 6.221 | 6.223 | 0.102 |
| 39.75, 22.75 | 2014-12-30T01:00:00 | 38 | wet_snow | 1.674 | 16.124 | 18.031 | 17.573 | 0.175 |
| 39.75, 22.25 | 2017-12-20T16:00:00 | 37 | wet_snow | 1.724 | 4.852 | 4.357 | 2.969 | 0.238 |
| 39.75, 22.00 | 2017-12-20T16:00:00 | 37 | wet_snow | 1.527 | 4.013 | 5.270 | 5.030 | 0.295 |

## Data-handling assumptions and cautions

- ERA5 `kg m-2 s-1` water-equivalent rates are converted to `mm h-1` by multiplying by 3,600.

- `ptype` is treated as an exact category and is never interpolated. Longitude is normalized to [-180°, 180°) and then sorted.

- A one-hour sample contributes one hour to occurrence counts. Event precipitation totals sum the hourly mean rates over those one-hour intervals.

- Missing cloud-base height remains missing rather than being imputed; it commonly indicates that a meaningful cloud base is unavailable for that sample.

- The minimum derived dewpoint depression is slightly below zero (about -0.003 °C), a negligible packing/rounding artefact retained rather than clipped.

- ECMWF describes `ptype` as an instantaneous diagnostic to be used with precipitation rate. In this archive, many flagged observations coincide with trace or zero interval-mean precipitation, so unfiltered event counts should not be read as verified accretion hours.

- These are gridded ERA5 values, not site observations or validated conductor ice accretion. Wet snow is retained separately from freezing liquid because the mechanisms differ.

## Reusable outputs

- `validation_manifest.csv`
- `general_conditions.csv`
- `precipitation_type_occurrence.csv`
- `conditional_statistics.csv`
- `ptype_sensitivity.csv`
- `ptype_diagnostics.csv`
- `event_extremes.csv`
- `per_grid_cell_summary.csv`
- `spatial_domain_summary.csv`
- `numerical_report.md`

## Recommended next step

Review the detected episodes against independent station observations or synoptic records and decide whether an evidence-backed trace-precipitation rule is needed. Then expand the archive toward a climatologically meaningful period before running the same configuration-driven pipeline for western Montana.

## Definitions

Precipitation-type labels follow [ECMWF/WMO GRIB2 Code Table 4.201](https://codes.ecmwf.int/grib/format/grib2/ctables/4/201/) and the [ECMWF ptype parameter description](https://codes.ecmwf.int/grib/param-db/260015).
