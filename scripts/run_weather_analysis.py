#!/usr/bin/env python3
"""Run the complete configured ERA5 numerical-analysis pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nesc_weather.config import load_config
from nesc_weather.pipeline import run_pipeline


def parse_years(value: str | None) -> set[int] | None:
    if value is None:
        return None
    years: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            start_text, end_text = item.split(":", maxsplit=1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise argparse.ArgumentTypeError(f"Invalid descending year range: {item}")
            years.update(range(start, end + 1))
        else:
            years.add(int(item))
    if not years:
        raise argparse.ArgumentTypeError("Year selection is empty")
    return years


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/larisa.yaml")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument(
        "--years",
        help="Comma-separated years and/or inclusive ranges, e.g. 2013:2020,2022.",
    )
    parser.add_argument(
        "--no-derived-netcdf",
        action="store_true",
        help="Skip the Git-ignored merged/derived NetCDF cache.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    result = run_pipeline(
        config,
        data_root=args.data_root,
        output_root=args.output_root,
        years=parse_years(args.years),
        write_derived_dataset=not args.no_derived_netcdf,
    )
    print(f"Processed years: {result.years[0]}–{result.years[-1]} ({len(result.years)})")
    print(f"Validated files: {len(result.manifest)}")
    print(f"Report: {result.report_path}")
    if not args.no_derived_netcdf:
        print(f"Derived dataset: {result.derived_dataset_path}")


if __name__ == "__main__":
    main()
