"""Acquire one raw ERA5 year folder from Google Drive using gdown."""

from __future__ import annotations

from pathlib import Path


def download_drive_year(folder_url: str, output_dir: Path) -> Path:
    """Download a public/shared Google Drive year folder into output_dir."""
    try:
        import gdown
    except ImportError as exc:
        raise RuntimeError("gdown is required for Google Drive acquisition") from exc

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = gdown.download_folder(
        url=folder_url,
        output=str(output_dir),
        quiet=False,
        use_cookies=False,
        remaining_ok=True,
    )
    if result is None:
        raise RuntimeError(f"gdown failed to download folder {folder_url}")
    return output_dir
