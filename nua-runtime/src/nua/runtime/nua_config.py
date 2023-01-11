"""Wrapper for the "nua-config.toml" file."""
import json
from pathlib import Path
from typing import Any

import tomli
import yaml
from nua.lib.panic import abort

from .constants import NUA_CONFIG_EXT, NUA_CONFIG_STEM

REQUIRED_BLOCKS = ["metadata"]
REQUIRED_METADATA = ["id", "version", "title", "author", "licence"]
OPTIONAL_METADATA = ["tagline", "website", "tags", "profile", "release", "changelog"]


def nua_config_names():
    for suffix in NUA_CONFIG_EXT:
        yield f"{NUA_CONFIG_STEM}.{suffix}"


class NuaConfig:
    """Wrapper for the "nua-config.toml" file.

    The config file can be any of nua-config.[toml|json|yaml|yml]"""

    path: Path
    root_dir: Path
    _data: dict

    def __init__(self, path: str | Path | None = None):
        if not path:
            path = ""
        self._find_config_file(path)
        self._loads_config()
        self._check()
        self.root_dir = self.path.parent

    def _find_config_file(self, path: Path | str) -> None:
        path = Path(path).resolve()
        if path.is_file():
            path = path.parent
        if path.is_dir():
            for name in nua_config_names():
                test_path = path / name
                if test_path.is_file():
                    self.path = test_path
                    return
        abort(f"Nua config file not found in: '{path}'")
        raise SystemExit(1)

    def _loads_config(self):
        if self.path.suffix == ".toml":
            self._data = tomli.loads(self.path.read_text(encoding="utf8"))
        elif self.path.suffix in {".json", ".yaml", ".yml"}:
            self._data = yaml.safe_load(self.path.read_text(encoding="utf8"))
        else:
            abort(f"Unknown file extension for '{self.path}'")
            raise SystemExit(1)

    def as_dict(self) -> dict:
        return self._data

    def dump_json(self, folder: Path | str) -> None:
        dest = Path(folder) / f"{NUA_CONFIG_STEM}.json"
        dest.write_text(
            json.dumps(self._data, sort_keys=False, ensure_ascii=False, indent=4),
            encoding="utf8",
        )

    def _check(self):
        for block in REQUIRED_BLOCKS:
            if block not in self._data:
                abort(f"Missing mandatory block in {self.path}: '{block}'")
        if "build" not in self._data:
            self._data["build"] = {}
        for key in REQUIRED_METADATA:
            if key not in self._data["metadata"]:
                abort(f"Missing mandatory metadata in {self.path}: '{key}'")

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
