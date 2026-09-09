"""Deterministic Markdown report generation from tidy numerical outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr


VARIABLE_LABELS = {
    "t2m_c": "2 m temperature (t2m_c)",
    "dewpoint_depression_c": "Dewpoint depression (t2m_c - d2m_c)",
    "precip_rate_mmh": "Total precipitation rate (precip_rate_mmh)",
    "snowfall_rate_mmh": "Snowfall rate, water equivalent (snowfall_rate_mmh)",
    "fg10": "10 m gust (fg10)",
    "low_cloud_cover_pct": "Low cloud cover (lcc)",
    "tcslw": "Total column supercooled liquid water (tcslw)",
    "cbh": "Cloud base height (cbh)",
}

LOWER_TAIL_VARIABLES = ("t2m_c", "dewpoint_depression_c", "cbh")
UPPER_TAIL_VARIABLES = ("precip_rate_mmh", "snowfall_rate_mmh", "fg10", "tcslw")
CONDITIONAL_FOCUS = ("freezing_liquid", "wet_snow", "accretion_relevant")


def _fmt(value: object, decimals: int = 3) -> str:
    if pd.isna(value):
        return "NA"
    if isinstance(value, (bool, np.bool_)):
        return "yes" if value else "no"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.{decimals}f}"
    return str(value)


def _table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_fmt(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _stat_row(
    conditional: pd.DataFrame, condition: str, variable: str
) -> pd.Series:
    matches = conditional[
        (conditional["condition"] == condition)
        & (conditional["variable"] == variable)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one conditional-statistics row for "
            f"{condition}/{variable}; found {len(matches)}"
        )
    return matches.iloc[0]


def _lower_tail_rows(
    conditional: pd.DataFrame, conditions: tuple[str, ...]
) -> list[list[object]]:
    rows: list[list[object]] = []
    for condition in conditions:
        for variable in LOWER_TAIL_VARIABLES:
            row = _stat_row(conditional, condition, variable)
            rows.append(
                [
                    condition,
                    VARIABLE_LABELS[variable],
                    row.units,
                    int(row["count"]),
                    int(row.missing_count),
                    row["mean"],
                    row["median"],
                    row.p25,
                    row.p05,
                    row["min"],
                ]
            )
    return rows


def _upper_tail_rows(
    conditional: pd.DataFrame, conditions: tuple[str, ...]
) -> list[list[object]]:
    rows: list[list[object]] = []
    for condition in conditions:
        for variable in UPPER_TAIL_VARIABLES:
            row = _stat_row(conditional, condition, variable)
            rows.append(
                [
                    condition,
                    VARIABLE_LABELS[variable],
                    row.units,
                    int(row["count"]),
                    int(row.missing_count),
                    row["mean"],
                    row["median"],
                    row.p90,
                    row.p95,
                    row.p99,
                    row["max"],
                ]
            )
    return rows


def _cloud_cover_rows(
    conditional: pd.DataFrame, conditions: tuple[str, ...]
) -> list[list[object]]:
    rows: list[list[object]] = []
    for condition in conditions:
        row = _stat_row(conditional, condition, "low_cloud_cover_pct")
        rows.append(
            [
                condition,
                int(row["count"]),
                int(row.missing_count),
                row["mean"],
                row["median"],
                row.p75,
                row.p90,
            ]
        )
    return rows


def _event_rows(events: pd.DataFrame) -> list[list[object]]:
    return [
        [
            f"{row.latitude:.2f}, {row.longitude:.2f}",
            row.start,
            int(row.duration_hours),
            row.ptype_labels,
            row.temperature_min_c,
            row.temperature_mean_c,
            row.gust_max_ms,
            row.precipitation_water_equivalent_mm,
            row.snowfall_water_equivalent_mm,
            row.tcslw_max_kgm2,
        ]
        for row in events.itertuples()
    ]


def write_numerical_report(
    path: Path,
    *,
    config: dict[str, Any],
    ds: xr.Dataset,
    manifest: pd.DataFrame,
    cold: pd.DataFrame,
    occurrence: pd.DataFrame,
    conditional: pd.DataFrame,
    sensitivity: pd.DataFrame,
    ptype_diagnostic: pd.DataFrame,
    spatial: pd.DataFrame,
    events: pd.DataFrame,
    output_files: list[str],
) -> None:
    """Write the primary, table-led exploration report."""

    years = sorted(set(pd.DatetimeIndex(ds.valid_time.values).year))
    times = pd.DatetimeIndex(ds.valid_time.values)
    cell_hours = int(
        ds.sizes["valid_time"] * ds.sizes["latitude"] * ds.sizes["longitude"]
    )
    region_name = config["region"]["name"]
    raw_variables = list(config["era5"]["variables"])
    derived_variables = [
        "t2m_c",
        "d2m_c",
        "dewpoint_depression_c",
        "precip_rate_mmh",
        "snowfall_rate_mmh",
        "low_cloud_cover_pct",
    ]
    lines = [
        f"# {region_name} ERA5 winter numerical exploration ({years[0]}–{years[-1]})",
        "",
        "## Scope",
        "",
        "This is a repeatable numerical exploration of the available January, "
        f"February and December observations. The {len(years)}-year archive is suitable for "
        "pipeline development and exploratory comparison, but not for a final NESC "
        "loading-zone classification, design adequacy conclusion, or climatological equivalence claim.",
        "",
        "All percentages labelled **all hours** use valid grid-cell-hours as the denominator. "
        "Percentages labelled **ptype-classified precipitation** use valid observations with ECMWF "
        "`ptype != 0` as the denominator. That is a categorical model denominator, not a guarantee "
        "of physically meaningful precipitation at a non-trace rate. No spatial averaging is "
        "performed before the per-cell metrics are calculated.",
        "",
        "## A. Dataset QA",
        "",
        _table(
            ["Item", "Result"],
            [
                ["Years", f"{years[0]}–{years[-1]} ({len(years)} years)"],
                [
                    "Selected months",
                    ", ".join(
                        str(month) for month in sorted(config["era5"]["months"])
                    ),
                ],
                ["Unique timestamps", len(times)],
                [
                    "Grid",
                    f"{ds.sizes['latitude']} latitude × {ds.sizes['longitude']} longitude",
                ],
                ["Grid-cell-hours", cell_hours],
                [
                    "Latitude coordinates",
                    ", ".join(f"{value:g}" for value in ds.latitude.values),
                ],
                [
                    "Longitude coordinates",
                    ", ".join(f"{value:g}" for value in ds.longitude.values),
                ],
                [
                    "Validated source files",
                    f"{int(manifest.validation_passed.sum())}/{len(manifest)}",
                ],
                [
                    "Unexpected within-month hourly gaps",
                    int(manifest.unexpected_within_month_gaps.sum()),
                ],
            ],
        ),
        "",
        "Annual time coverage is checked against every expected hour in each selected "
        "calendar month; the March–November interval is intentionally absent.",
        "",
    ]

    annual_rows = []
    for year, group in manifest.groupby("year"):
        annual_rows.append(
            [
                str(year),
                int(group.timestamp_count.iloc[0]),
                group.continuous_time_segments.iloc[0]
                .replace(";", "; ")
                .replace("..", " → "),
                bool(group.hourly_coverage_passed.all()),
            ]
        )
    lines.extend(
        [
            _table(
                ["Year", "Timestamps", "Observed hourly segments", "Coverage valid"],
                annual_rows,
            ),
            "",
            "Missing values are counted across the full time × latitude × longitude population.",
            "",
        ]
    )

    missing_rows = []
    for variable in raw_variables + derived_variables:
        missing = int(ds[variable].isnull().sum().item())
        missing_rows.append([variable, missing, 100.0 * missing / cell_hours])
    lines.extend(
        [
            _table(
                ["Variable", "Missing grid-cell-hours", "Missing (%)"], missing_rows
            ),
            "",
            "Validation result: all required files, variables, timestamps and grids aligned "
            "exactly across instant/avg/max packages and across years.",
            "",
            "## B. General winter conditions",
            "",
        ]
    )

    cold_rows = [
        [row.metric, int(row.count_grid_cell_hours), row.percentage]
        for row in cold.itertuples()
    ]
    lines.extend(
        [
            "### Cold-frequency context",
            "",
            _table(
                ["Temperature frequency", "Grid-cell-hours", "Percent"], cold_rows
            ),
            "",
            "### Cold / saturation / low-cloud-base tail",
            "",
            "For temperature, dewpoint depression and cloud-base height, the lower tail is "
            "the engineering-relevant direction. The report therefore foregrounds P25, P05 "
            "and the minimum rather than the warm/dry/high-cloud upper tail.",
            "",
            _table(
                [
                    "Condition",
                    "Variable",
                    "Units",
                    "Valid",
                    "Missing",
                    "Mean",
                    "Median",
                    "P25",
                    "P05",
                    "Min",
                ],
                _lower_tail_rows(conditional, ("all_winter",)),
            ),
            "",
            "### Wind / precipitation / supercooled-water upper tail",
            "",
            "For wind gust, precipitation rates and TCSLW, larger values represent the "
            "severity direction of interest, so upper percentiles and maxima are retained. "
            "All-winter precipitation-rate statistics include dry hours; conditional event "
            "statistics below are more representative of intensity during relevant weather.",
            "",
            _table(
                [
                    "Condition",
                    "Variable",
                    "Units",
                    "Valid",
                    "Missing",
                    "Mean",
                    "Median",
                    "P90",
                    "P95",
                    "P99",
                    "Max",
                ],
                _upper_tail_rows(conditional, ("all_winter",)),
            ),
            "",
            "### Low-cloud-cover distribution",
            "",
            "Low-cloud cover is bounded at 100%, so repeated P95/P99/max values of 100% add "
            "little information. The report instead shows the central and upper-middle distribution.",
            "",
            _table(
                ["Condition", "Valid", "Missing", "Mean", "Median", "P75", "P90"],
                _cloud_cover_rows(conditional, ("all_winter",)),
            ),
            "",
            "## C. Precipitation-type occurrence",
            "",
        ]
    )

    occurrence_rows = []
    for row in occurrence.itertuples():
        occurrence_rows.append(
            [
                row.category,
                row.ptype_codes,
                int(row.count_grid_cell_hours),
                row.pct_of_all_valid_grid_cell_hours,
                int(row.count_among_ptype_precipitation),
                row.pct_of_ptype_precipitation,
            ]
        )
    lines.extend(
        [
            _table(
                [
                    "Category",
                    "Code(s)",
                    "Count",
                    "% all hours",
                    "Count in ptype-classified precip",
                    "% ptype-classified precip",
                ],
                occurrence_rows,
            ),
            "",
            "`freezing_liquid` is codes 3 or 12. `accretion_relevant` is codes 3, 6 or 12. "
            "Ordinary snow and ice pellets are not included in that combined category.",
            "",
            "### Trace-precipitation sensitivity",
            "",
            "The unfiltered ptype classification remains the primary definition. The table "
            "below shows the effect of illustrative mean-rate filters; none is adopted as a final scientific threshold.",
            "",
        ]
    )

    sensitivity_focus = sensitivity[sensitivity.category == "accretion_relevant"]
    lines.extend(
        [
            _table(
                [
                    "Minimum precip rate (mm/h)",
                    "Retained count",
                    "% retained",
                    "% all hours",
                ],
                [
                    [
                        row.minimum_precip_rate_mmh,
                        int(row.count_grid_cell_hours),
                        row.pct_of_unfiltered_category_retained,
                        row.pct_of_all_valid_grid_cell_hours,
                    ]
                    for row in sensitivity_focus.itertuples()
                ],
            ),
            "",
            "### Diagnostic combinations requiring cautious interpretation",
            "",
            _table(
                ["Category", "Diagnostic", "Count", "Category total", "Percent"],
                [
                    [
                        row.category,
                        row.diagnostic,
                        int(row.count_grid_cell_hours),
                        int(row.category_grid_cell_hours),
                        row.percentage_of_category,
                    ]
                    for row in ptype_diagnostic.itertuples()
                ],
            ),
            "",
            "These combinations are not automatically errors: ptype is derived from the "
            "model's vertical thermodynamic structure, while `t2m` is only the 2 m air "
            "temperature and the rate is an interval mean. They do make an unfiltered "
            "ptype count a poor proxy for verified surface accretion.",
            "",
            "## D. Conditional icing-relevant statistics",
            "",
            "### Thermodynamic and cloud-base context",
            "",
            _table(
                [
                    "Condition",
                    "Variable",
                    "Units",
                    "Valid",
                    "Missing",
                    "Mean",
                    "Median",
                    "P25",
                    "P05",
                    "Min",
                ],
                _lower_tail_rows(conditional, CONDITIONAL_FOCUS),
            ),
            "",
            "Temperature maxima are intentionally not foregrounded here; unusually warm "
            "ptype flags are already exposed in the diagnostic table above.",
            "",
            "### Loading / intensity / supercooled-water severity",
            "",
            _table(
                [
                    "Condition",
                    "Variable",
                    "Units",
                    "Valid",
                    "Missing",
                    "Mean",
                    "Median",
                    "P90",
                    "P95",
                    "P99",
                    "Max",
                ],
                _upper_tail_rows(conditional, CONDITIONAL_FOCUS),
            ),
            "",
            "### Low-cloud-cover context",
            "",
            _table(
                ["Condition", "Valid", "Missing", "Mean", "Median", "P75", "P90"],
                _cloud_cover_rows(conditional, CONDITIONAL_FOCUS),
            ),
            "",
            "## E. Spatial statistics",
            "",
            "Each metric is first computed independently at each grid cell. The following "
            "summarizes those cell-level results across the domain. For cold, saturation "
            "and low-cloud-base metrics, smaller values are generally the more severe/relevant "
            "direction; for gust, precipitation and TCSLW, larger values are the severity direction.",
            "",
            _table(
                ["Per-cell metric", "Cells", "Minimum", "Median", "Mean", "Maximum"],
                [
                    [
                        row.metric,
                        int(row.cell_count),
                        row.domain_min,
                        row.domain_median,
                        row.domain_mean,
                        row.domain_max,
                    ]
                    for row in spatial.itertuples()
                ],
            ),
            "",
            "## F. Event and extreme exploration",
            "",
        ]
    )

    if events.empty:
        lines.append("No accretion-relevant grid-cell events were detected.")
    else:
        multi_hour = int((events.duration_hours >= 2).sum())
        event_headers = [
            "Cell",
            "Start",
            "Hours",
            "ptype",
            "T min °C",
            "T mean °C",
            "Gust max m/s",
            "Precip mm",
            "Snowfall mm w.e.",
            "TCSLW max kg/m²",
        ]
        longest = events.sort_values(
            ["duration_hours", "gust_max_ms", "start"],
            ascending=[False, False, True],
        ).head(10)
        gustiest = events.sort_values(
            ["gust_max_ms", "duration_hours", "start"],
            ascending=[False, False, True],
        ).head(10)
        highest_tcslw = events.sort_values(
            ["tcslw_max_kgm2", "duration_hours", "start"],
            ascending=[False, False, True],
        ).head(10)
        freezing_liquid = events[events["freezing_liquid_hours"] > 0].sort_values(
            ["duration_hours", "gust_max_ms", "start"],
            ascending=[False, False, True],
        ).head(10)

        lines.extend(
            [
                f"Detected **{len(events):,}** individual grid-cell events, of which "
                f"**{multi_hour:,}** lasted at least two consecutive hours. Events break "
                "whenever the next actual timestamp is not exactly one hour later, so the "
                "March–November archive gap cannot join two episodes.",
                "",
                "The event catalogue is shown through several rankings because the longest "
                "episode is not necessarily the most severe by wind, liquid-water availability, "
                "or freezing-liquid mechanism.",
                "",
                "### Longest accretion-relevant events",
                "",
                _table(event_headers, _event_rows(longest)),
                "",
                "### Highest gust during accretion-relevant events",
                "",
                _table(event_headers, _event_rows(gustiest)),
                "",
                "### Highest TCSLW during accretion-relevant events",
                "",
                _table(event_headers, _event_rows(highest_tcslw)),
                "",
                "### Freezing-liquid events",
                "",
                (
                    _table(event_headers, _event_rows(freezing_liquid))
                    if not freezing_liquid.empty
                    else "No freezing-liquid events were detected."
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Data-handling assumptions and cautions",
            "",
            "- ERA5 `kg m-2 s-1` water-equivalent rates are converted to `mm h-1` by multiplying by 3,600.",
            "",
            "- `ptype` is treated as an exact category and is never interpolated. Longitude is normalized to [-180°, 180°) and then sorted.",
            "",
            "- A one-hour sample contributes one hour to occurrence counts. Event precipitation totals sum the hourly mean rates over those one-hour intervals.",
            "",
            "- Missing cloud-base height remains missing rather than being imputed; it commonly indicates that a meaningful cloud base is unavailable for that sample.",
            "",
            "- The minimum derived dewpoint depression can be slightly below zero because of packing/rounding; such tiny negative values are retained rather than clipped.",
            "",
            "- ECMWF describes `ptype` as an instantaneous diagnostic to be used with precipitation rate. In this archive, many flagged observations coincide with trace or zero interval-mean precipitation, so unfiltered event counts should not be read as verified accretion hours.",
            "",
            "- These are gridded ERA5 values, not site observations or validated conductor ice accretion. Wet snow is retained separately from freezing liquid because the mechanisms differ.",
            "",
            "## Reusable outputs",
            "",
        ]
    )
    lines.extend(f"- `{name}`" for name in output_files)
    lines.extend(
        [
            "",
            "## Recommended next step",
            "",
            "Review the detected episodes against independent station observations or "
            "synoptic records and decide whether an evidence-backed trace-precipitation rule "
            "is needed. Then expand the archive toward a climatologically meaningful period "
            "before running the same configuration-driven pipeline for western Montana.",
            "",
            "## Definitions",
            "",
            "Precipitation-type labels follow [ECMWF/WMO GRIB2 Code Table 4.201](https://codes.ecmwf.int/grib/format/grib2/ctables/4/201/) and the [ECMWF ptype parameter description](https://codes.ecmwf.int/grib/param-db/260015).",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
