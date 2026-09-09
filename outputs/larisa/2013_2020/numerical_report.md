# Larisa ERA5 winter numerical exploration (2013–2020)

## Scope

This is the first repeatable numerical exploration of the available January, February and December observations. The eight-year archive is suitable for pipeline development and exploratory comparison, but not for a final NESC loading-zone classification, design adequacy conclusion, or climatological equivalence claim.

All percentages labelled **all hours** use valid grid-cell-hours as the denominator. Percentages labelled **ptype precipitation** use valid observations with ECMWF `ptype != 0` as the denominator. No spatial averaging is performed before the per-cell metrics are calculated.

## A. Dataset QA

| Item | Result |
| --- | --- |
| Years | 2013–2020 (8 years) |
| Selected months | 1, 2, 12 |
| Unique timestamps | 17,328 |
| Grid | 5 latitude × 5 longitude |
| Grid-cell-hours | 433,200 |
| Latitude coordinates | 40.25, 40, 39.75, 39.5, 39.25 |
| Longitude coordinates | 21.75, 22, 22.25, 22.5, 22.75 |
| Validated source files | 24/24 |
| Unexpected within-month hourly gaps | 0 |

Annual time coverage is checked against every expected hour in each selected calendar month; the March–November interval is intentionally absent.

| Year | Timestamps | Observed hourly segments | Coverage valid |
| --- | --- | --- | --- |
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
| cbh | 104,746 | 24.180 |
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
| t2m_at_or_below_0_c | 46,849 | 10.815 |
| t2m_at_or_below_-5_c | 5,423 | 1.252 |
| t2m_at_or_below_-10_c | 518 | 0.120 |

| Variable | Units | Valid | Missing | Mean | Median | P95 | P99 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| t2m_c | degC | 433,200 | 0 | 6.428 | 6.722 | 14.030 | 16.948 | 24.878 |
| dewpoint_depression_c | degC | 433,200 | 0 | 4.542 | 3.561 | 11.688 | 15.328 | 33.693 |
| precip_rate_mmh | mm h-1 | 433,200 | 0 | 0.116 | 0.000 | 0.672 | 1.894 | 8.659 |
| snowfall_rate_mmh | mm h-1 water equivalent | 433,200 | 0 | 0.017 | 0.000 | 0.036 | 0.470 | 5.478 |
| fg10 | m s-1 | 433,200 | 0 | 5.365 | 4.640 | 11.124 | 15.143 | 29.362 |
| low_cloud_cover_pct | percent | 433,200 | 0 | 34.446 | 15.433 | 100.000 | 100.000 | 100.000 |
| tcslw | kg m-2 | 433,200 | 0 | 0.035 | 0.002 | 0.195 | 0.352 | 1.370 |
| cbh | m | 328,454 | 104,746 | 1,255.885 | 563.524 | 5,983.286 | 8,475.465 | 14,010.276 |

## C. Precipitation-type occurrence

| Category | Code(s) | Count | % all hours | Count in ptype precip | % ptype precip |
| --- | --- | --- | --- | --- | --- |
| freezing_rain | 3 | 831 | 0.192 | 831 | 0.411 |
| freezing_drizzle | 12 | 0 | 0.000 | 0 | 0.000 |
| freezing_liquid | 3;12 | 831 | 0.192 | 831 | 0.411 |
| wet_snow | 6 | 9,273 | 2.141 | 9,273 | 4.582 |
| accretion_relevant | 3;6;12 | 10,104 | 2.332 | 10,104 | 4.993 |
| rain | 1 | 167,758 | 38.725 | 167,758 | 82.894 |
| ordinary_snow | 5 | 18,382 | 4.243 | 18,382 | 9.083 |
| rain_and_snow | 7 | 3,145 | 0.726 | 3,145 | 1.554 |
| ice_pellets | 8 | 2,988 | 0.690 | 2,988 | 1.476 |
| thunderstorm | 2 | 0 | 0.000 | 0 | 0.000 |
| no_precipitation | 0 | 230,823 | 53.283 | 0 | 0.000 |

`freezing_liquid` is codes 3 or 12. `accretion_relevant` is codes 3, 6 or 12. Ordinary snow and ice pellets are not included in that combined category.

### Trace-precipitation sensitivity

The unfiltered ptype classification remains the primary definition. The table below shows the effect of illustrative mean-rate filters; none is adopted as a final scientific threshold.

| Minimum precip rate (mm/h) | Retained count | % retained | % all hours |
| --- | --- | --- | --- |
| 0.000 | 10,104 | 100.000 | 2.332 |
| 0.010 | 6,770 | 67.003 | 1.563 |
| 0.100 | 4,031 | 39.895 | 0.931 |

### Diagnostic combinations requiring cautious interpretation

| Category | Diagnostic | Count | Category total | Percent |
| --- | --- | --- | --- | --- |
| freezing_liquid | zero_interval_mean_precip_rate | 98 | 831 | 11.793 |
| freezing_liquid | precip_rate_below_0.01_mmh | 506 | 831 | 60.890 |
| freezing_liquid | t2m_above_0_c | 424 | 831 | 51.023 |
| freezing_liquid | t2m_above_2_c | 36 | 831 | 4.332 |
| wet_snow | zero_interval_mean_precip_rate | 897 | 9,273 | 9.673 |
| wet_snow | precip_rate_below_0.01_mmh | 2,828 | 9,273 | 30.497 |
| wet_snow | t2m_above_5_c | 148 | 9,273 | 1.596 |

These combinations are not automatically errors: ptype is derived from the model's vertical thermodynamic structure, while `t2m` is only the 2 m air temperature and the rate is an interval mean. They do make an unfiltered ptype count a poor proxy for verified surface accretion.

## D. Conditional icing-relevant statistics

| Condition | Variable | Units | Valid | Missing | Mean | Median | P95 | P99 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_winter | t2m_c | degC | 433,200 | 0 | 6.428 | 6.722 | 14.030 | 16.948 | 24.878 |
| all_winter | dewpoint_depression_c | degC | 433,200 | 0 | 4.542 | 3.561 | 11.688 | 15.328 | 33.693 |
| all_winter | precip_rate_mmh | mm h-1 | 433,200 | 0 | 0.116 | 0.000 | 0.672 | 1.894 | 8.659 |
| all_winter | snowfall_rate_mmh | mm h-1 water equivalent | 433,200 | 0 | 0.017 | 0.000 | 0.036 | 0.470 | 5.478 |
| all_winter | fg10 | m s-1 | 433,200 | 0 | 5.365 | 4.640 | 11.124 | 15.143 | 29.362 |
| all_winter | low_cloud_cover_pct | percent | 433,200 | 0 | 34.446 | 15.433 | 100.000 | 100.000 | 100.000 |
| all_winter | tcslw | kg m-2 | 433,200 | 0 | 0.035 | 0.002 | 0.195 | 0.352 | 1.370 |
| all_winter | cbh | m | 328,454 | 104,746 | 1,255.885 | 563.524 | 5,983.286 | 8,475.465 | 14,010.276 |
| freezing_liquid | t2m_c | degC | 831 | 0 | -0.036 | 0.033 | 1.931 | 2.480 | 2.944 |
| freezing_liquid | dewpoint_depression_c | degC | 831 | 0 | 1.036 | 0.789 | 2.619 | 3.701 | 5.949 |
| freezing_liquid | precip_rate_mmh | mm h-1 | 831 | 0 | 0.059 | 0.005 | 0.304 | 1.188 | 2.062 |
| freezing_liquid | snowfall_rate_mmh | mm h-1 water equivalent | 831 | 0 | 0.005 | 0.000 | 0.010 | 0.119 | 0.719 |
| freezing_liquid | fg10 | m s-1 | 831 | 0 | 4.108 | 3.603 | 7.666 | 10.273 | 17.492 |
| freezing_liquid | low_cloud_cover_pct | percent | 831 | 0 | 63.099 | 70.874 | 100.000 | 100.000 | 100.000 |
| freezing_liquid | tcslw | kg m-2 | 831 | 0 | 0.035 | 0.018 | 0.127 | 0.248 | 0.369 |
| freezing_liquid | cbh | m | 803 | 28 | 434.023 | 153.674 | 2,204.901 | 3,221.498 | 7,365.747 |
| wet_snow | t2m_c | degC | 9,273 | 0 | 1.977 | 2.051 | 4.178 | 5.339 | 7.750 |
| wet_snow | dewpoint_depression_c | degC | 9,273 | 0 | 4.973 | 4.433 | 11.341 | 13.754 | 16.791 |
| wet_snow | precip_rate_mmh | mm h-1 | 9,273 | 0 | 0.277 | 0.058 | 1.339 | 2.610 | 5.714 |
| wet_snow | snowfall_rate_mmh | mm h-1 water equivalent | 9,273 | 0 | 0.240 | 0.049 | 1.146 | 2.334 | 5.478 |
| wet_snow | fg10 | m s-1 | 9,273 | 0 | 7.073 | 6.338 | 13.838 | 16.019 | 19.694 |
| wet_snow | low_cloud_cover_pct | percent | 9,273 | 0 | 64.302 | 77.612 | 100.000 | 100.000 | 100.000 |
| wet_snow | tcslw | kg m-2 | 9,273 | 0 | 0.082 | 0.053 | 0.260 | 0.382 | 1.104 |
| wet_snow | cbh | m | 9,173 | 100 | 728.761 | 616.787 | 1,818.112 | 2,796.632 | 5,556.848 |
| accretion_relevant | t2m_c | degC | 10,104 | 0 | 1.812 | 1.929 | 4.127 | 5.293 | 7.750 |
| accretion_relevant | dewpoint_depression_c | degC | 10,104 | 0 | 4.649 | 4.042 | 11.181 | 13.670 | 16.791 |
| accretion_relevant | precip_rate_mmh | mm h-1 | 10,104 | 0 | 0.259 | 0.048 | 1.298 | 2.540 | 5.714 |
| accretion_relevant | snowfall_rate_mmh | mm h-1 water equivalent | 10,104 | 0 | 0.221 | 0.034 | 1.108 | 2.263 | 5.478 |
| accretion_relevant | fg10 | m s-1 | 10,104 | 0 | 6.829 | 6.021 | 13.673 | 15.975 | 19.694 |
| accretion_relevant | low_cloud_cover_pct | percent | 10,104 | 0 | 64.203 | 77.174 | 100.000 | 100.000 | 100.000 |
| accretion_relevant | tcslw | kg m-2 | 10,104 | 0 | 0.078 | 0.049 | 0.255 | 0.373 | 1.104 |
| accretion_relevant | cbh | m | 9,976 | 128 | 705.037 | 578.807 | 1,825.893 | 2,880.092 | 7,365.747 |

## E. Spatial statistics

Each metric is first computed independently at each grid cell. The following summarizes those 25 cell-level results across the domain.

| Per-cell metric | Cells | Minimum | Median | Mean | Maximum |
| --- | --- | --- | --- | --- | --- |
| t2m_c_mean | 25 | 3.562 | 6.539 | 6.428 | 10.168 |
| t2m_at_or_below_0_c_pct | 25 | 0.491 | 11.756 | 10.815 | 22.726 |
| t2m_at_or_below_minus_5_c_pct | 25 | 0.000 | 1.125 | 1.252 | 3.186 |
| t2m_at_or_below_minus_10_c_pct | 25 | 0.000 | 0.063 | 0.120 | 0.485 |
| fg10_p95 | 25 | 7.640 | 10.583 | 10.659 | 14.475 |
| fg10_max | 25 | 17.225 | 21.608 | 21.946 | 29.362 |
| precip_rate_mmh_mean | 25 | 0.082 | 0.115 | 0.116 | 0.172 |
| precip_rate_mmh_max | 25 | 4.056 | 5.825 | 6.058 | 8.659 |
| tcslw_mean | 25 | 0.026 | 0.035 | 0.035 | 0.042 |
| tcslw_max | 25 | 0.519 | 0.850 | 0.899 | 1.370 |
| freezing_liquid_pct_all_hours | 25 | 0.000 | 0.115 | 0.192 | 0.814 |
| wet_snow_pct_all_hours | 25 | 1.016 | 1.841 | 2.141 | 4.051 |
| accretion_relevant_pct_all_hours | 25 | 1.125 | 1.979 | 2.332 | 4.444 |
| event_count | 25 | 32.000 | 93.000 | 104.560 | 247.000 |
| maximum_event_duration_hours | 25 | 16.000 | 23.000 | 28.600 | 50.000 |

## F. Event and extreme exploration

Detected **2,614** individual grid-cell events, of which **1,732** lasted at least two consecutive hours. Events break whenever the next actual timestamp is not exactly one hour later, so the March–November archive gap cannot join two episodes.

| Cell | Start | Hours | ptype | T mean °C | Gust max m/s | Precip mm | Snowfall mm w.e. | TCSLW max kg/m² |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40.00, 22.75 | 2014-12-30T02:00:00 | 50 | wet_snow | 1.761 | 16.827 | 11.916 | 11.590 | 0.148 |
| 40.00, 22.50 | 2014-12-30T02:00:00 | 50 | wet_snow | -1.489 | 14.563 | 10.731 | 10.732 | 0.106 |
| 39.75, 21.75 | 2017-12-20T15:00:00 | 47 | wet_snow | 1.241 | 5.456 | 8.371 | 7.990 | 0.344 |
| 40.25, 22.75 | 2014-12-30T05:00:00 | 45 | wet_snow | 1.896 | 14.508 | 4.975 | 4.793 | 0.124 |
| 40.25, 22.50 | 2014-12-30T05:00:00 | 45 | wet_snow | -1.260 | 12.359 | 6.221 | 6.223 | 0.102 |
| 39.75, 22.75 | 2014-12-30T01:00:00 | 38 | wet_snow | 1.674 | 16.124 | 18.031 | 17.573 | 0.175 |
| 39.75, 22.25 | 2017-12-20T16:00:00 | 37 | wet_snow | 1.724 | 4.852 | 4.357 | 2.969 | 0.238 |
| 39.75, 22.00 | 2017-12-20T16:00:00 | 37 | wet_snow | 1.527 | 4.013 | 5.270 | 5.030 | 0.295 |
| 39.50, 22.75 | 2019-02-23T08:00:00 | 36 | wet_snow | 2.057 | 19.694 | 22.667 | 20.828 | 0.242 |
| 39.50, 22.75 | 2014-12-31T09:00:00 | 32 | wet_snow | 2.058 | 16.273 | 7.926 | 7.888 | 0.166 |

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
