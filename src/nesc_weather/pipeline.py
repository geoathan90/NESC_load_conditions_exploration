"""End-to-end archive validation, preprocessing, analysis and output writing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import xarray as xr

from .config import PipelineConfig
from .discovery import discover_year_files
from .events import detect_accretion_events, event_counts_by_cell
from .preprocessing import derive_analysis_variables
from .report import write_numerical_report
from .statistics import (
    cold_frequency,
    conditional_statistics,
    per_grid_cell_summary,
    precipitation_type_occurrence,
    ptype_diagnostics,
    ptype_sensitivity,
    spatial_domain_summary,
)
from .validation import validate_archive


@dataclass(frozen=True)
class PipelineResult:
    years: tuple[int, ...]
    output_root: Path
    report_path: Path
    derived_dataset_path: Path
    dataset: xr.Dataset
    manifest: pd.DataFrame


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.10g")


def run_pipeline(
    config: PipelineConfig,
    *,
    data_root: Path | None = None,
    output_root: Path | None = None,
    years: set[int] | None = None,
    write_derived_dataset: bool = True,
) -> PipelineResult:
    """Run the complete configured archive pipeline and write reusable outputs."""

    source_root = config.data_root(data_root)
    discovered = discover_year_files(source_root, config.era5["files"])
    if years is not None:
        missing = sorted(years - discovered.keys())
        if missing:
            raise ValueError(f"Requested years not found: {missing}")
        discovered = {year: discovered[year] for year in sorted(years)}
    selected_years = tuple(sorted(discovered))
    dataset, manifest = validate_archive(discovered, config.era5, config.region)
    manifest["path"] = manifest["path"].map(
        lambda value: Path(value).resolve().relative_to(source_root.resolve()).as_posix()
    )
    dataset = derive_analysis_variables(dataset)
    period_name = f"{selected_years[0]}_{selected_years[-1]}"
    target_root = (
        Path(output_root).expanduser().resolve()
        if output_root is not None
        else config.output_root() / period_name
    )
    target_root.mkdir(parents=True, exist_ok=True)

    events = detect_accretion_events(
        dataset,
        minimum_duration_hours=int(config.analysis["event_minimum_duration_hours"]),
    )
    cells = per_grid_cell_summary(dataset, event_counts_by_cell(events))
    frames = {
        "validation_manifest.csv": manifest,
        "general_conditions.csv": cold_frequency(
            dataset, config.analysis["cold_thresholds_c"]
        ),
        "precipitation_type_occurrence.csv": precipitation_type_occurrence(dataset),
        "conditional_statistics.csv": conditional_statistics(dataset),
        "ptype_sensitivity.csv": ptype_sensitivity(
            dataset, config.analysis["precipitation_sensitivity_thresholds_mmh"]
        ),
        "ptype_diagnostics.csv": ptype_diagnostics(dataset),
        "event_extremes.csv": events,
        "per_grid_cell_summary.csv": cells,
        "spatial_domain_summary.csv": spatial_domain_summary(cells),
    }
    for name, frame in frames.items():
        _write_csv(frame, target_root / name)

    derived_path = config.derived_root() / period_name / "analysis_dataset.nc"
    if write_derived_dataset:
        derived_path.parent.mkdir(parents=True, exist_ok=True)
        encoding = {
            variable: {"zlib": True, "complevel": 4}
            for variable in dataset.data_vars
        }
        dataset.to_netcdf(derived_path, engine="h5netcdf", encoding=encoding)

    report_path = target_root / "numerical_report.md"
    write_numerical_report(
        report_path,
        config=config.values,
        ds=dataset,
        manifest=manifest,
        cold=frames["general_conditions.csv"],
        occurrence=frames["precipitation_type_occurrence.csv"],
        conditional=frames["conditional_statistics.csv"],
        sensitivity=frames["ptype_sensitivity.csv"],
        ptype_diagnostic=frames["ptype_diagnostics.csv"],
        spatial=frames["spatial_domain_summary.csv"],
        events=events,
        output_files=[*frames.keys(), "numerical_report.md"],
    )
    return PipelineResult(
        years=selected_years,
        output_root=target_root,
        report_path=report_path,
        derived_dataset_path=derived_path,
        dataset=dataset,
        manifest=manifest,
    )
