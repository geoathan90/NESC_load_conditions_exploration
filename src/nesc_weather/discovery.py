"""Local source-file discovery."""

from __future__ import annotations

import re
from pathlib import Path

YEAR_RE = re.compile(r"^\d{4}$")


def discover_year_files(
    data_root: Path, expected_files: dict[str, str]
) -> dict[int, dict[str, Path]]:
    """Discover four-digit year directories and require one file per step type."""

    if not data_root.is_dir():
        raise FileNotFoundError(f"Data root does not exist: {data_root}")
    years: dict[int, dict[str, Path]] = {}
    for directory in sorted(data_root.iterdir()):
        if not directory.is_dir() or YEAR_RE.fullmatch(directory.name) is None:
            continue
        year = int(directory.name)
        paths = {step: directory / name for step, name in expected_files.items()}
        missing = [path.name for path in paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                f"Year {year} is incomplete; missing: {', '.join(sorted(missing))}"
            )
        years[year] = paths
    if not years:
        raise FileNotFoundError(f"No four-digit year directories found in {data_root}")
    return years
