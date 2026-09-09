"""Configuration loading and path resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PipelineConfig:
    """Validated pipeline configuration plus its source location."""

    values: dict[str, Any]
    path: Path

    @property
    def region(self) -> dict[str, Any]:
        return self.values["region"]

    @property
    def era5(self) -> dict[str, Any]:
        return self.values["era5"]

    @property
    def analysis(self) -> dict[str, Any]:
        return self.values["analysis"]

    @property
    def source(self) -> dict[str, Any]:
        return self.values["source"]

    def resolve_repo_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.path.parent.parent / path).resolve()

    def data_root(self, override: str | Path | None = None) -> Path:
        if override is not None:
            return Path(override).expanduser().resolve()
        storage = self.values["storage"]
        env_name = storage["data_root_env"]
        configured = os.environ.get(env_name, storage["default_data_root"])
        return self.resolve_repo_path(configured)

    def output_root(self, override: str | Path | None = None) -> Path:
        if override is not None:
            return Path(override).expanduser().resolve()
        return self.resolve_repo_path(self.values["storage"]["output_root"])

    def derived_root(self) -> Path:
        return self.resolve_repo_path(self.values["storage"]["derived_root"])


def load_config(path: str | Path) -> PipelineConfig:
    """Load a YAML configuration and fail early on missing core sections."""

    config_path = Path(path).expanduser().resolve()
    with config_path.open(encoding="utf-8") as handle:
        values = yaml.safe_load(handle)
    if not isinstance(values, dict):
        raise ValueError(f"Configuration must be a mapping: {config_path}")
    required = {"region", "era5", "storage", "source", "analysis"}
    missing = sorted(required - values.keys())
    if missing:
        raise ValueError(f"Configuration is missing sections: {', '.join(missing)}")
    return PipelineConfig(values=values, path=config_path)
