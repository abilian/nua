"""Wrapper for the "nua-config.toml" file."""
from pathlib import Path
from typing import Any

import tomli
from nua.lib.panic import abort

from .constants import NUA_CONFIG

REQUIRED_BLOCKS = ["metadata", "build"]
REQUIRED_METADATA = ["id", "version", "title", "author", "licence"]
OPTIONAL_METADATA = ["tagline", "website", "tags", "profile", "release", "changelog"]


class NuaConfig:
    """Wrapper for the "nua-config.toml" file."""

    path: Path
    root_dir: Path
    _data: dict

    def __init__(self, filename: str | Path | None = None):
        if not filename:
            filename = NUA_CONFIG
        self.path = Path(filename).resolve()
        if self.path.is_dir():
            self.path = self.path / NUA_CONFIG
        if not self.path.is_file():
            abort(f"File not found '{self.path}'")

        with self.path.open(mode="rb") as config_file:
            self._data = tomli.load(config_file)
        self._check()
        self.root_dir = self.path.parent

    def as_dict(self) -> dict:
        return self._data

    def _check(self):
        for block in REQUIRED_BLOCKS:
            if block not in self._data:
                abort(f"Missing mandatory block in {NUA_CONFIG}: '{block}'")
        for key in REQUIRED_METADATA:
            if key not in self._data["metadata"]:
                abort(f"Missing mandatory metadata in {NUA_CONFIG}: '{key}'")

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
    def src_url(self) -> str:
        if base := self.metadata.get("src_url"):
            return base.format(**self.metadata)
        return ""

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
    def meta_packages(self) -> list:
        return self.build.get("meta-packages", [])

    @property
    def packages(self) -> list:
        return self.build.get("packages", [])

    @property
    def build_packages(self) -> list:
        return self.build.get("build-packages", [])

    @property
    def profile(self) -> str:
        """Profile of image and required version.

        Example or returned value:
            for standard:
                {}
            for nodejs:
                {"node": ">=14.13.1,<17"}
        """
        return self["profile"]
