#!/usr/bin/env python3
"""Incrementally synchronize the configured public Drive folder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nesc_weather.acquisition import sync_drive_folder
from nesc_weather.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/larisa.yaml")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download existing non-empty files instead of incrementally skipping them.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    data_root = config.data_root(args.data_root)
    manifest = sync_drive_folder(
        config.source["google_drive_root_url"],
        data_root,
        overwrite=args.overwrite,
        quiet=args.quiet,
    )
    manifest["local_path"] = manifest["local_path"].map(
        lambda value: Path(value).resolve().relative_to(data_root).as_posix()
    )
    manifest_path = config.resolve_repo_path(config.values["storage"]["drive_manifest"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    counts = manifest["status"].value_counts().to_dict()
    # Transfer action is intentionally excluded so a successful re-run is deterministic.
    manifest.drop(columns="status").to_csv(manifest_path, index=False)
    print(f"Discovered {len(manifest)} files across {manifest['year'].nunique()} years")
    print("Statuses:", ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
