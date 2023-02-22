"""Wrapper for the "nua-config.toml" file."""
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import tomli
import yaml
from nua.lib.actions import download_extract
from nua.lib.panic import abort

from .constants import NUA_CONFIG_EXT, NUA_CONFIG_STEM
from .nua_tag import nua_tag_string

REQUIRED_BLOCKS = ["metadata"]
REQUIRED_METADATA = ["id", "version", "title", "author", "license"]
OPTIONAL_METADATA = ["tagline", "website", "tags", "profile", "release", "changelog"]
# blocks added (empty) if not present in orig file:
COMPLETE_BLOCKS = ["build", "env", "docker"]


def nua_config_names():
    for suffix in NUA_CONFIG_EXT:
        yield f"{NUA_CONFIG_STEM}.{suffix}"


def hyphen_get(data: dict, key: str, default: Any = None) -> Any:
    """Return value from dict for key either hyphen "-" or underscore "_" in it,
    priority to "-".
    """
    if (hypkey := key.replace("_", "-")) in data:
        result = data.get(hypkey)
    elif (underkey := key.replace("-", "_")) in data:
        result = data.get(underkey)
    else:
        result = default
    return result


def nomalize_env_values(env: dict) -> dict:
    validated: dict[str, str | dict] = {}
    for key, value in env.items():
        if isinstance(value, dict):
            validated[key] = {k: normalize_env_leaf(v) for k, v in value.items()}
        else:
            validated[key] = normalize_env_leaf(value)
    return deepcopy(validated)


def normalize_env_leaf(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, list)):
        return str(value)
    abort(f"ENV value has wrong type: '{value}'")
    raise SystemExit(1)


class NuaConfig:
    """Wrapper for the "nua-config.toml" file.

    The config file can be any of nua-config.[toml|json|yaml|yml]
    """

    path: Path
    root_dir: Path
    _data: dict

    def __init__(self, path: str | Path | None = None):
        if not path:
            path = "."
        self._find_config_file(path)
        self._loads_config()
        self._check_required_blocks()
        self._complete_missing_blocks()
        self._fix_spelling()
        self._check_required_metadata()
        self._check_checksum_format()
        self._nomalize_env_values()
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

    def _check_required_blocks(self):
        for block in REQUIRED_BLOCKS:
            if block not in self._data:
                abort(f"Missing mandatory block in {self.path}: '{block}'")

    def _complete_missing_blocks(self):
        for block in COMPLETE_BLOCKS:
            if block not in self._data:
                self._data[block] = {}

    def _fix_spelling(self):
        if "license" not in self.metadata and "licence" in self.metadata:
            self.metadata["license"] = self.metadata["licence"]

    def _check_required_metadata(self):
        for key in REQUIRED_METADATA:
            if key not in self._data["metadata"]:
                abort(f"Missing mandatory metadata in {self.path}: '{key}'")

    def _check_checksum_format(self):
        checksum = self.checksum
        if not checksum:
            return
        if checksum.startswith("sha256:"):
            checksum = checksum[7:]
        if len(checksum) != 64:
            abort(f"Wrong checksum content (expecting 64 length sha256): {checksum}")
        self.metadata["checksum"] = checksum

    def _nomalize_env_values(self):
        self._data["env"] = nomalize_env_values(self.env)

    def __getitem__(self, key: str) -> Any:
        """will return {} is key not found, assuming some parts are not
        mandatory and first level element are usually dict."""
        return self._data.get(key) or {}

    # metadata ######################################################

    @property
    def metadata(self) -> dict:
        return self["metadata"]

    @property
    def version(self) -> str:
        """version of package source."""
        return self.metadata.get("version", "")

    @property
    def src_url(self) -> str:
        if base := hyphen_get(self.metadata, "src-url"):
            return base.format(**self.metadata)
        return ""

    @property
    def checksum(self) -> str:
        """Return checksum associated to 'src-url' or null string."""
        return self.metadata.get("checksum", "").strip().lower()

    @property
    def app_id(self) -> str:
        return self.metadata.get("id", "")

    @property
    def nua_tag(self) -> str:
        return nua_tag_string(self.metadata)

    # build #########################################################

    @property
    def build(self) -> dict:
        return self["build"]

    @property
    def builder(self) -> dict:
        return self.build.get("builder", "")

    @property
    def project(self) -> str:
        """The project URL to build with autodetection."""
        if base := self.build.get("project"):
            return base.format(**self.metadata)
        return ""

    @property
    def manifest(self) -> list:
        return self.build.get("manifest", [])

    @property
    def meta_packages(self) -> list:
        return hyphen_get(self.build, "meta-packages", [])

    @property
    def packages(self) -> list:
        # use alias for run-packages
        run_packages = hyphen_get(self.build, "run-packages", [])
        if not run_packages:
            # previous name
            run_packages = self.build.get("packages", [])
        return run_packages

    @property
    def build_packages(self) -> list:
        return hyphen_get(self.build, "build-packages", [])

    @property
    def pip_install(self) -> list:
        return hyphen_get(self.build, "pip-install", [])

    # env ###########################################################

    @property
    def env(self) -> dict:
        return self["env"]

    # docker env ####################################################

    @property
    def docker(self) -> dict:
        return self["docker"]

    # resource ######################################################

    @property
    def resource(self) -> list:
        """The list of resources (tag 'resource')."""
        return self._data.get("resource", [])

    # actions #######################################################

    def fetch_source(self) -> Path | None:
        """Download, check and extract source URL, returning the source Path."""
        return download_extract(self.src_url, "/nua/build", self.checksum)