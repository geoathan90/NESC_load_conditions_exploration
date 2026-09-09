"""Incremental Google Drive folder discovery and download."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import gdown
import pandas as pd

YEAR_PATH_RE = re.compile(r"^(?P<year>\d{4})/(?P<name>[^/]+)$")


@dataclass(frozen=True)
class RemoteFile:
    year: int
    filename: str
    drive_id: str
    relative_path: str
    local_path: str


def discover_drive_files(root_url: str, data_root: Path) -> list[RemoteFile]:
    """Recursively discover stored (non-Google-native) files below a Drive root."""

    discovered = gdown.download_folder(
        url=root_url,
        output=str(data_root),
        quiet=True,
        use_cookies=False,
        skip_download=True,
    )
    files: list[RemoteFile] = []
    seen_paths: set[str] = set()
    for item in discovered:
        relative = Path(item.path).as_posix()
        match = YEAR_PATH_RE.fullmatch(relative)
        if match is None:
            raise ValueError(
                "Drive source must contain files directly under four-digit year "
                f"folders; found {relative!r}"
            )
        if relative in seen_paths:
            raise ValueError(f"Drive source contains duplicate path: {relative}")
        seen_paths.add(relative)
        files.append(
            RemoteFile(
                year=int(match.group("year")),
                filename=match.group("name"),
                drive_id=item.id,
                relative_path=relative,
                local_path=str(Path(item.local_path).resolve()),
            )
        )
    return sorted(files, key=lambda item: (item.year, item.filename))


def sync_drive_folder(
    root_url: str,
    data_root: Path,
    *,
    overwrite: bool = False,
    quiet: bool = False,
) -> pd.DataFrame:
    """Download missing Drive files atomically and return a machine-readable manifest."""

    data_root.mkdir(parents=True, exist_ok=True)
    remote_files = discover_drive_files(root_url, data_root)
    rows: list[dict[str, object]] = []
    for remote in remote_files:
        destination = Path(remote.local_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        was_present = destination.is_file() and destination.stat().st_size > 0
        status = "skipped_existing"
        if overwrite or not was_present:
            partial = destination.with_suffix(destination.suffix + ".part")
            result = gdown.download(
                id=remote.drive_id,
                output=str(partial),
                quiet=quiet,
                use_cookies=False,
                resume=True,
            )
            if result is None or not partial.is_file() or partial.stat().st_size == 0:
                raise RuntimeError(f"Download failed for {remote.relative_path}")
            os.replace(partial, destination)
            status = "overwritten" if was_present else "downloaded"
        row = asdict(remote)
        row.update(
            {
                "status": status,
                "local_exists": destination.is_file(),
                "local_size_bytes": destination.stat().st_size,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)
