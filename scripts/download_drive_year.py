"""Download one Google Drive ERA5 year folder into the canonical raw-data location."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nesc_weather.acquire import download_drive_year  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Google Drive year-folder URL")
    parser.add_argument("--output", type=Path, required=True, help="Destination year folder")
    args = parser.parse_args()
    path = download_drive_year(args.url, args.output)
    print(f"Downloaded to {path}")


if __name__ == "__main__":
    main()
