from pathlib import Path

import pytest

from nesc_weather.discovery import discover_year_files


FILES = {
    "instant": "instant.nc",
    "avg": "avg.nc",
    "max": "max.nc",
}


def test_discovers_complete_year_directories(tmp_path: Path) -> None:
    for year in (2013, 2014):
        directory = tmp_path / str(year)
        directory.mkdir()
        for filename in FILES.values():
            (directory / filename).touch()
    (tmp_path / "notes").mkdir()
    result = discover_year_files(tmp_path, FILES)
    assert list(result) == [2013, 2014]
    assert result[2014]["max"].name == "max.nc"


def test_incomplete_year_fails_clearly(tmp_path: Path) -> None:
    directory = tmp_path / "2020"
    directory.mkdir()
    (directory / "instant.nc").touch()
    with pytest.raises(FileNotFoundError, match="Year 2020 is incomplete"):
        discover_year_files(tmp_path, FILES)
