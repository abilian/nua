"""Wrapper for the "nua-config.toml" file."""
from pathlib import Path
from typing import Any

import toml

from .constants import NUA_CONFIG
from .scripting import panic


class NuaConfig:
    """Wrapper for the "nua-config.toml" file."""

    def __init__(self, filename=NUA_CONFIG, folder=""):
        if folder:
            self.path = Path(folder).resolve() / Path(filename)
        else:
            self.path = Path(filename).resolve()
        if not self.path.is_file():
            panic(f"Error: File not found '{self.path}'")
        with open(self.path, encoding="utf8") as config_file:
            self._data = toml.load(config_file)

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
    def src_url(self) -> str:
        src_url = self.build.get("src_url") or ""
        if "{" in src_url and self.version:
            src_url = src_url.format(version=self.version)

        return src_url

    @property
    def src_git(self) -> str:
        return self.build.get("src_git") or ""
