from pathlib import Path
from types import SimpleNamespace

import pytest

from nesc_weather import acquisition


def test_drive_discovery_uses_year_relative_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    items = [
        SimpleNamespace(
            path="2021/data_stream-oper_stepType-instant.nc",
            local_path=str(tmp_path / "2021" / "data_stream-oper_stepType-instant.nc"),
            id="file-id",
        )
    ]
    monkeypatch.setattr(acquisition.gdown, "download_folder", lambda **kwargs: items)
    result = acquisition.discover_drive_files("https://example.invalid/folder", tmp_path)
    assert result[0].year == 2021
    assert result[0].filename == "data_stream-oper_stepType-instant.nc"
    assert result[0].drive_id == "file-id"


def test_sync_skips_existing_nonempty_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    destination = tmp_path / "2022" / "source.nc"
    destination.parent.mkdir()
    destination.write_bytes(b"existing")
    remote = acquisition.RemoteFile(
        year=2022,
        filename="source.nc",
        drive_id="file-id",
        relative_path="2022/source.nc",
        local_path=str(destination),
    )
    monkeypatch.setattr(acquisition, "discover_drive_files", lambda *args: [remote])

    def unexpected_download(**kwargs):
        raise AssertionError("existing files should not be downloaded")

    monkeypatch.setattr(acquisition.gdown, "download", unexpected_download)
    manifest = acquisition.sync_drive_folder("unused", tmp_path, quiet=True)
    assert manifest.loc[0, "status"] == "skipped_existing"
    assert manifest.loc[0, "local_size_bytes"] == len(b"existing")
