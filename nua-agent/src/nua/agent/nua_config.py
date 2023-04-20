"""Class to manage the "nua-config.toml" file."""
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Union

import tomli
import yaml
from nua.lib.actions import download_extract
from nua.lib.shell import chown_r

from .constants import NUA_CONFIG_EXT, NUA_CONFIG_STEM
from .nua_tag import nua_tag_string

REQUIRED_BLOCKS = ["metadata"]
REQUIRED_METADATA = ["id", "version", "title", "author", "license"]
OPTIONAL_METADATA = [
    "tagline",
    "website",
    "tags",
    "profile",
    "release",
    "changelog",
    "name",
    "image",
]
# blocks added (empty) if not present in orig file:
COMPLETE_BLOCKS = ["build", "run", "env", "docker"]


class NuaConfigError(ValueError):
    pass


def nua_config_names():
    for suffix in NUA_CONFIG_EXT:
        yield f"{NUA_CONFIG_STEM}.{suffix}"


def hyphen_get(data: dict, key: str, default: Any = None) -> Any:
    """Return value from dict for key either hyphen "-" or underscore "_" in
    it, priority to "-"."""
    if (hypkey := key.replace("_", "-")) in data:
        result = data.get(hypkey)
    elif (underkey := key.replace("-", "_")) in data:
        result = data.get(underkey)
    else:
        result = default
    return result


def nomalize_env_values(env: dict[str, Union[str, int, float, list]]) -> dict[str, str]:
    def normalize_env_leaf(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, list)):
            return str(value)
        raise NuaConfigError(f"ENV value has wrong type: '{value}'")

    validated: dict[str, str | dict] = {}
    for key, value in env.items():
        if isinstance(value, dict):
            validated[key] = {k: normalize_env_leaf(v) for k, v in value.items()}
        else:
            validated[key] = normalize_env_leaf(value)

    return deepcopy(validated)  # type: ignore


def force_list(content: str | list[str]) -> list[str]:
    """Return always a list, if a single string is provided, wrap it into
    list."""
    if isinstance(content, list):
        return content
    if isinstance(content, str) and content:
        return [content]
    return []


class NuaConfig:
    """Class to manage the "nua-config.toml" file.

    The config file can be any of nua-config.[toml|json|yaml|yml]
    """

    path: Path
    root_dir: Path
    nua_dir_exists: bool
    _data: dict

    def __init__(self, path: str | Path | None = None):
        if not path:
            path = "."
        self._find_root_dir(path)
        self._find_config_file()
        self._loads_config()
        self._check_required_blocks()
        self._complete_missing_blocks()
        self._fix_spelling()
        self._check_required_metadata()
        self._check_checksum_format()
        self._nomalize_env_values()

    def __repr__(self):
        return f"NuaConfig(path={self.path}, id={id(self)})"

    def _find_root_dir(self, path: Path | str) -> None:
        """Find project folder.

        Analyses structure of parameters:

        Below the expected structure of folders. 'nua' folder and subfolders are
        optional, the 'nua-config' file can be at 3 positions: 'project', 'nua'
        subfolder, or 'metadata' subfolder.

        The path parameter can be:
            - the 'nua-config' file
            - the path of 'nua' folder, 'project' folder or folder containing the
              'nua-config' file

        We try to:
            - find the 'nua-file'
            - find the 'project' path
            - find the 'nua' path (if exists)

        The 'nua-config' file used is the one of higher level found.

        /project
            ...project code source...
            nua-config
            /nua
                Dockerfile
                build.py
                ...
                nua-config
                /metadata
                    nua-config
                /build
                   ...files to copy...
                /app
                   ...files to copy...
        """
        path = Path(path).resolve()
        if path.is_dir():
            folder = path
        else:
            folder = path.parent
        if folder.name == "nua":
            self.root_dir = folder.parent
        elif folder.name == "metadata" and folder.parent.name == "nua":
            self.root_dir = folder.parent.parent
        else:
            self.root_dir = folder
        self.nua_dir_exists = (self.root_dir / "nua").is_dir()

    def _find_config_file(self):
        """Find nua-config file."""
        for folder in (
            self.root_dir,
            self.root_dir / "nua",
            self.root_dir / "nua" / "metadata",
        ):
            if not folder.is_dir():
                continue
            for name in nua_config_names():
                test_path = folder / name
                if test_path.is_file():
                    self.path = test_path
                    return

        raise NuaConfigError(
            f"Nua config file not found in '{self.root_dir}' and sub folders"
        )

    def _loads_config(self):
        if self.path.suffix == ".toml":
            self._data = tomli.loads(self.path.read_text(encoding="utf8"))
        elif self.path.suffix in {".json", ".yaml", ".yml"}:
            self._data = yaml.safe_load(self.path.read_text(encoding="utf8"))
        else:
            raise NuaConfigError(f"Unknown file extension for '{self.path}'")

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
                raise NuaConfigError(
                    f"Missing mandatory block in {self.path}: '{block}'"
                )

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
                raise NuaConfigError(
                    f"Missing mandatory metadata in {self.path}: '{key}'"
                )

    def _check_checksum_format(self):
        checksum = self.checksum
        if not checksum:
            return
        if checksum.startswith("sha256:"):
            checksum = checksum[7:]
        if len(checksum) != 64:
            raise NuaConfigError(
                f"Wrong checksum content (expecting 64 length sha256): {checksum}"
            )
        self.metadata["checksum"] = checksum

    def _nomalize_env_values(self):
        self._data["env"] = nomalize_env_values(self.env)

    def __getitem__(self, key: str) -> Any:
        """will return {} if key not found, assuming some parts are not
        mandatory and first level element are usually dict."""
        return self._data.get(key) or {}

    # metadata ######################################################

    @property
    def metadata(self) -> dict:
        return self["metadata"]

    @property
    def metadata_rendered(self) -> dict:
        """Return the metadata dict with rendered f-string values."""
        data = {}
        for key, val in deepcopy(self.metadata).items():
            if isinstance(val, str):
                data[key] = val.format(**self.metadata)
            else:
                data[key] = val
        return data

    @property
    def version(self) -> str:
        """Version of package source."""
        return self.metadata.get("version", "")

    @property
    def src_url(self) -> str:
        if base := hyphen_get(self.metadata, "src-url"):
            return base.format(**self.metadata)
        return ""

    @property
    def git_url(self) -> str:
        if base := hyphen_get(self.metadata, "git-url"):
            return base.format(**self.metadata)
        return ""

    @property
    def git_branch(self) -> str:
        if base := hyphen_get(self.metadata, "git-branch"):
            return base.format(**self.metadata)
        return "main"

    @property
    def wrap_image(self) -> str:
        """Optional  Docker 'image' to be used as base for 'wrap' strategy.

        If the 'image' metadata is defined, the build strategy is to add
        the '/nua/metadata/nua-config.json' file on the declared image,
        when build method is 'wrap'.
        """
        if base := self.metadata.get("image", ""):
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
    def name(self) -> str:
        if name := self.metadata.get("name", ""):
            return name
        return self.app_id

    @property
    def nua_tag(self) -> str:
        return nua_tag_string(self.metadata)

    # build #########################################################

    @property
    def build(self) -> dict:
        return self["build"]

    @property
    def builder(self) -> str:
        return self.build.get("builder", "")

    @property
    def project(self) -> str:
        """The project URL to build with autodetection."""
        if base := self.build.get("project"):
            return base.format(**self.metadata)
        return ""

    @property
    def manifest(self) -> list:
        return force_list(self.build.get("manifest", []))

    @property
    def meta_packages(self) -> list:
        return force_list(hyphen_get(self.build, "meta-packages", []))

    @property
    def build_packages(self) -> list:
        return force_list(self.build.get("packages", []))

    @property
    def build_command(self) -> list:
        """Return the list of build commands, each cmd rendered with
        metadata."""
        metadata = self.metadata_rendered
        commands = []
        for cmd in force_list(hyphen_get(self.build, "build-command", [])):
            if isinstance(cmd, str):
                commands.append(cmd.format(**metadata))
            else:
                commands.append(cmd)
        return commands

    @property
    def pip_install(self) -> list:
        return force_list(hyphen_get(self.build, "pip-install", []))

    @property
    def build_method(self) -> str:
        """Build method (or default build method).

        Can be empty string if not defined (then autodetection from
        metadata).
        """
        default_method = hyphen_get(self.build, "default-method", "")
        return self.build.get("method", default_method)

    @property
    def docker_user(self) -> str:
        """User of the Docker container, default is root.

        Especially usefull when wrapping an existing Dockerfile.
        """
        return hyphen_get(self.build, "docker-user", "")

    # run ###########################################################

    @property
    def run(self) -> dict:
        return self["run"]

    @property
    def packages(self) -> list:
        "Return list of run packages (packages remanent after build)."
        return force_list(self.run.get("packages", []))

    @property
    def start_command(self) -> list:
        return force_list(hyphen_get(self.run, "start", []))

    # env ###########################################################

    @property
    def env(self) -> dict:
        return self["env"]

    # docker env ####################################################

    @property
    def docker(self) -> dict:
        return self["docker"]

    # volumes declaration ###########################################

    @property
    def volume(self) -> list:
        """The list of declared volumes."""
        return self._data.get("volume", [])

    # resource ######################################################

    @property
    def resource(self) -> list:
        """The list of resources (tag 'resource')."""
        return self._data.get("resource", [])

    # actions #######################################################

    def fetch_source(self, name: str = "") -> Path:
        """Download, check and extract source URL, returning the source Path.

        Set ownership to 'nua' user if launched by 'root'.
        """
        if not name:
            name = self.name
            if name.startswith("nua-"):
                name = name[4:]
        path = download_extract(self.src_url, "/nua/build", name, self.checksum)
        if os.getuid() == 0:
            chown_r(path, "nua")
        return path
