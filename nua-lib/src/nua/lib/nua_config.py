"""Class to manage the "nua-config.toml" file."""
import json
import os
from copy import deepcopy
from functools import cached_property
from pathlib import Path
from typing import Any

import tomli
import yaml
from dictdiffer import diff

from .actions import download_extract, to_kebab_cases, to_snake_cases
from .constants import NUA_CONFIG_STEM, nua_config_names
from .exceptions import NuaConfigError
from .normalization import normalize_env_values, normalize_ports, ports_as_list
from .nua_config_format import NuaConfigFormat
from .nua_tag import nua_tag_string
from .panic import red_line, vprint
from .shell import chown_r

# blocks added (empty) if not present in orig file:
COMPLETE_BLOCKS = ["build", "run", "env", "docker"]


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


def force_list(content: Any) -> list[Any]:
    """Return always a list, if a single string is provided, wrap it into
    list.
    >>> force_list("foo")
    ['foo']
    >>> force_list(["foo", "bar"])
    ['foo', 'bar']
    >>> force_list([])
    []
    >>> force_list("")
    []
    """
    if content is None or content == "":
        return []
    match content:
        case list():
            return content
        case _:
            return [content]


class NuaConfig:
    """Class to manage the "nua-config.toml" file.

    The config file can be any of nua-config.[toml|json|yaml|yml]
    """

    path: Path
    root_dir: Path
    nua_dir_exists: bool
    _data: dict[str, Any]

    def __init__(self, path: str | Path | None = None):
        if not path:
            path = "."
        self._find_root_dir(path)
        self._find_config_file()
        self._loads_config()
        self._check_checksum_format()
        self._normalize_env_values()
        self._normalize_ports()

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

    def _read_config_data(self) -> dict[str, Any]:
        if self.path.suffix == ".toml":
            return tomli.loads(self.path.read_text(encoding="utf8"))
        elif self.path.suffix in {".json", ".yaml", ".yml"}:
            return yaml.safe_load(self.path.read_text(encoding="utf8"))
        else:
            raise NuaConfigError(f"Unknown file extension for '{self.path}'")

    def _loads_config(self) -> None:
        unchanged = {"docker", "env"}
        recurse = 4
        read_data = self._read_config_data()
        data = deepcopy(read_data)
        to_snake_cases(data, recurse=recurse, unchanged=unchanged)
        # store internally as a dict() after pydantic validation:
        data = NuaConfigFormat(**data).dict()
        to_kebab_cases(data, recurse=recurse, unchanged=unchanged)
        self._data = data
        self._show_config_differences(read_data)

    def _show_config_differences(self, data: dict[str, Any]) -> None:
        """Print the difference between original data and actual loaded config.

        This shows the diff between the original TOML and the parsed config once
        it has been converted to a Pydantic model.
        Pydantic doesn't check (AFAIK) for extra (just for missing keys or values
        of the wrong type), so this is a way to check for typos in the keys, etc.
        """
        header_displayed = False
        for key, section, changes in diff(data, self._data):
            if len(changes) == 2 and not isinstance(changes[0], tuple):
                change_list = [changes]
            else:
                change_list = changes
            for change_key, value in change_list:
                if value is None:
                    continue
                if not header_displayed:
                    red_line("NuaConfig data changes:")
                    header_displayed = True
                vprint(f"    {key}: {section}.{change_key}: {repr(value)}")

    def as_dict(self) -> dict[str, Any]:
        return self._data

    def dump_json(self, folder: Path | str) -> None:
        dest = Path(folder) / f"{NUA_CONFIG_STEM}.json"
        dest.write_text(
            json.dumps(self._data, sort_keys=False, ensure_ascii=False, indent=4),
            encoding="utf8",
        )

    def _check_checksum_format(self):
        checksum = self.src_checksum
        if not checksum:
            return
        if checksum.startswith("sha256:"):
            checksum = checksum[7:]
        if len(checksum) != 64:
            raise NuaConfigError(
                f"Wrong src-checksum content (expecting 64 length sha256): {checksum}"
            )

    def _normalize_env_values(self):
        self._data["env"] = normalize_env_values(self.env)

    def _normalize_ports(self):
        normalized_ports = normalize_ports(ports_as_list(self.ports))
        self._data["port"] = {}
        for port in normalized_ports:
            name = port["name"]
            del port["name"]
            self._data["port"][name] = port

    def __getitem__(self, key: str) -> Any:
        """will return {} if key not found, assuming some parts are not
        mandatory and first level element are usually dict."""
        return self._data.get(key) or {}

    # metadata ######################################################

    @property
    def metadata(self) -> dict:
        return self["metadata"]

    @cached_property
    def metadata_rendered(self) -> dict:
        """Return the metadata and build sections with rendered
        f-string values."""
        mixed = deepcopy(self.metadata)
        mixed.update(deepcopy(self.build))
        data = {}
        for key, val in deepcopy(mixed).items():
            if isinstance(val, str):
                data[key] = val.format(**mixed)
            else:
                data[key] = val
        return data

    @property
    def version(self) -> str:
        """Version of package source."""
        return self.metadata.get("version", "")

    @property
    def app_id(self) -> str:
        return self.metadata.get("id", "")

    @property
    def title(self) -> str:
        return self.metadata.get("title", "")

    @property
    def nua_tag(self) -> str:
        return nua_tag_string(self.metadata)

    # build #########################################################

    @property
    def build(self) -> dict:
        return self._data.get("build") or {}

    @cached_property
    def src_url(self) -> str:
        if base := hyphen_get(self.build, "src-url"):
            return base.format(**self.metadata_rendered)
        return ""  #

    @cached_property
    def git_url(self) -> str:
        if base := hyphen_get(self.build, "git-url"):
            return base.format(**self.metadata_rendered)
        return ""

    @cached_property
    def git_branch(self) -> str:
        if base := hyphen_get(self.build, "git-branch"):
            return base.format(**self.metadata_rendered)
        return "main"

    @cached_property
    def wrap_image(self) -> str:
        """Optional container image to be used as base for 'wrap' strategy.

        If the 'base-image' metadata is defined, the build strategy is to add
        the '/nua/metadata/nua-config.json' file on the declared image,
        when build method is 'wrap'.
        """
        if base := hyphen_get(self.build, "base-image"):
            return base.format(**self.metadata_rendered)
        return ""

    @property
    def src_checksum(self) -> str:
        """Return checksum associated to 'src-url' or null string."""
        if checksum := hyphen_get(self.build, "src-checksum"):
            return checksum.strip().lower()
        return ""  #

    @cached_property
    def builder(self) -> str | dict[str, str] | list[dict]:
        if base := self.build.get("builder", ""):
            if isinstance(base, str):
                return base.format(**self.metadata_rendered)
        return ""

    @cached_property
    def project(self) -> str:
        """The project URL to build with autodetection."""
        if base := self.build.get("project"):
            return base.format(**self.metadata_rendered)
        return ""

    @property
    def manifest(self) -> list:
        return force_list(self.build.get("manifest") or "")

    @property
    def meta_packages(self) -> list:
        return force_list(hyphen_get(self.build, "meta-packages") or "")

    @property
    def build_packages(self) -> list:
        return force_list(self.build.get("packages") or "")

    @cached_property
    def build_command(self) -> list:
        """Return the list of build commands, each cmd rendered with
        metadata."""
        commands = []
        for cmd in force_list(self.build.get("build", [])):
            if isinstance(cmd, str):
                commands.append(cmd.format(**self.metadata_rendered))
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

    # run ###########################################################

    @property
    def run(self) -> dict:
        return self._data.get("run") or {}

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
        return self._data.get("env") or {}

    # docker env ####################################################

    @property
    def docker(self) -> dict:
        return self._data.get("docker") or {}

    # volumes declaration ###########################################

    @property
    def volumes(self) -> list:
        """The list of declared volumes."""
        return self._data.get("volume") or []

    # providers #####################################################

    @property
    def providers(self) -> list:
        """The list of providers (tag 'provider')."""
        return self._data.get("provider") or []

    # ports #########################################################

    @property
    def ports(self) -> dict[str, dict]:
        return self._data.get("port") or {}

    # actions #######################################################

    def fetch_source(self, name: str = "") -> Path:
        """Download, check and extract source URL, returning the source Path.

        Set ownership to 'nua' user if launched by 'root'.
        """
        if not name:
            name = self.app_id
            if name.startswith("nua-"):
                name = name[4:]
        path = download_extract(self.src_url, "/nua/build", name, self.src_checksum)
        if os.getuid() == 0:
            chown_r(path, "nua")
        return path
