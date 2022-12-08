"""Wrapper for the "nua-config.toml" file."""
from pathlib import Path
from typing import Any

import tomli
from nua.lib.panic import error

from .constants import NUA_BUILDER_TAG, NUA_CONFIG
from .version import __version__

REQUIRED_BLOCKS = ["metadata", "build"]
REQUIRED = ["id", "version", "title", "author", "licence"]
OPTIONAL = ["tagline", "website", "tags", "profile", "release", "changelog"]


class NuaConfig:
    """Wrapper for the "nua-config.toml" file."""

    path: Path
    root_dir: Path

    def __init__(self, filename: str | Path | None = None):
        if not filename:
            filename = NUA_CONFIG
        self.path = Path(filename).resolve()
        if self.path.is_dir():
            self.path = self.path / NUA_CONFIG
        if not self.path.is_file():
            error(f"File not found '{self.path}'")
        with open(self.path, mode="rb") as config_file:
            self._data = tomli.load(config_file)
        self.root_dir = self.path.parent
        self.assert_format()

    def as_dict(self) -> dict:
        return self._data

    def assert_format(self):
        for block in REQUIRED_BLOCKS:
            if block not in self._data:
                error(f"missing mandatory '{block}' block in {NUA_CONFIG}")
        for key in REQUIRED:
            if key not in self._data["metadata"]:
                error(f"missing mandatory metadata in {NUA_CONFIG}: '{key}'")

    def __getitem__(self, key: str) -> Any:
        """will return {} is key not found, assuming some parts are not
        mandatory and first level element are usually dict."""
        return self._data.get(key) or {}

    @property
    def metadata(self) -> dict:
        return self["metadata"]

    @property
    def version(self) -> str:
        """version of package source."""
        return self.metadata.get("version", "")

    @property
    def app_id(self) -> str:
        return self.metadata.get("id", "")

    @property
    def build(self) -> dict:
        return self["build"]

    @property
    def manifest(self) -> list:
        return self.build.get("manifest", [])

    @property
    def source_url(self) -> str:
        source_url = self.build.get("source_url") or ""
        return source_url

    @property
    def nua_base(self) -> str:
        base = self.build.get("nua_base") or NUA_BUILDER_TAG
        if ":" not in base:
            base = f"{base}:{__version__}"
        return base
