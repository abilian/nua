from __future__ import annotations

from copy import deepcopy
from pprint import pformat
from typing import Any

from nua.lib.console import print_red
from nua.lib.panic import Abort

from .utils import get_alias, sanitized_name

# later, add 'npipe' when managed:
MANAGED = "managed"
DIRECTORY = "directory"
TMPFS = "tmpfs"
ALLOWED_TYPE = {MANAGED, DIRECTORY, TMPFS}
CHECKED_KEYS = {
    "_checked_",
    # "dest",
    # "destination",
    "domains",
    "driver",
    "backup",
    "options",
    # "source",
    "name",
    "_label",
    # "src",
    # "prefix",
    # "source-prefix",
    # "src-prefix",
    "target",
    "type",
}


class Volume:
    """Representation of a volume attached to a container, either the main app
    container or a Provider container."""

    def __init__(self):
        self._dict: dict[str, Any] = {}

    def __str__(self) -> str:
        lst = ["  "]
        lst.append(f"type={self.type}")
        if self.driver:
            lst.append(f"driver={self.driver}")
        if self.full_name:
            lst.append(f"full_name={self.full_name}")
        if self.domains:
            lst.append("\n   domains: " + ", ".join(self.domains))
        return " ".join(lst)

    def __setitem__(self, key: str, item: Any):
        self._dict[key] = item

    def __getitem__(self, key: str) -> Any:
        return self._dict[key]

    def has_key(self, key: int | str) -> bool:
        return key in self._dict

    def get(self, key: str, default=None) -> Any:
        return self._dict.get(key, default)

    @classmethod
    def parse(cls, data: dict) -> Volume:
        """Parse a python dict to obtain a Volume instance.

        Apply sanity checks if _checked_ is not present.
        """
        if not isinstance(data, dict):
            raise ValueError("'volume._dict' must be a dict")
        volume = Volume()
        if data.get("_checked_", False):
            volume._dict = data
        else:
            volume.check_load(data)
        return volume

    def check_load(self, data: dict):
        try:
            self._check_type(data)
            self._check_name(data)
            self._check_label(data)
            self._check_target(data)
            self._parse_domains(data)
            self._parse_options(data)
            self._parse_backup(data)
            self._dict["_checked_"] = True
        except ValueError as e:
            print_red(str(e))
            print_red(pformat(data))
            raise Abort("Volume configuration has errors")

    @classmethod
    def normalize_list(cls, volume_list: list[dict]) -> list[dict]:
        """Parse each dict of the list to ensure it is valid volume.

        Return a list of valid volumes exported as dicts.
        """
        return [cls.parse(data).as_dict() for data in volume_list]

    @classmethod
    def update_name_dict(cls, data: dict, label: str) -> dict:
        volume = cls.parse(data)
        volume.label = label
        return volume.as_dict()

    @classmethod
    def string(cls, data: dict) -> str:
        volume = cls.parse(data)
        return str(volume)

    @classmethod
    def from_dict(cls, data: dict) -> Volume:
        volume = cls()
        volume._dict = data
        return volume

    def as_dict(self) -> dict:
        return deepcopy(self._dict)

    def as_short_dict(self) -> dict[str, Any]:
        record = deepcopy(self._dict)
        return {
            key: val
            for key, val in record.items()
            if key not in {"label", "backup", "_checked_"}
        }

    @property
    def type(self) -> str:
        return self._dict.get("type") or MANAGED

    @type.setter
    def type(self, tpe: str):
        self._dict["type"] = tpe

    @property
    def is_managed(self) -> bool:
        return self.type == MANAGED

    @property
    def is_local(self) -> bool:
        return self.driver in {"docker", "local"}

    @property
    def driver(self) -> str:
        driver = self._dict.get("driver", "")
        if not driver and self.type == MANAGED:
            driver = "docker"
        return driver

    @driver.setter
    def driver(self, driver: str):
        self._dict["driver"] = driver

    @property
    def name(self) -> str:
        return self._dict.get("name") or ""

    @name.setter
    def name(self, name: str):
        self._dict["name"] = name

    @property
    def label(self) -> str:
        return self._dict.get("label") or ""

    @label.setter
    def label(self, label: str):
        self._dict["label"] = label

    @property
    def full_name(self) -> str:
        if not self.name:
            return ""
        if self.type == DIRECTORY:
            return self.name
        return sanitized_name(f"{self.label}-{self.name}")

    @property
    def target(self) -> str:
        return self._dict.get("target") or ""

    @target.setter
    def target(self, target: str):
        self._dict["target"] = target

    @property
    def domains(self) -> list[str]:
        return self._dict.get("domains") or []

    @domains.setter
    def domains(self, domains: list[str]):
        self._dict["domains"] = domains

    @property
    def options(self) -> dict:
        return self._dict.get("options") or {}

    @options.setter
    def options(self, options: dict):
        self._dict["options"] = options

    @property
    def backup(self) -> dict[str, Any]:
        return self._dict.get("backup") or {}

    @backup.setter
    def backup(self, backup: dict[str, Any]):
        self._dict["backup"] = backup

    def _check_type(self, data: dict):
        tpe = data.get("type") or MANAGED
        if tpe not in ALLOWED_TYPE:
            raise ValueError(f"Unknown value for 'volume.type': {tpe}")
        self.type = tpe
        if tpe == MANAGED:
            self.driver = data.get("driver") or "docker"

    def _check_name(self, data: dict):
        if self.type == TMPFS:
            # no source defined for "tmpfs" type
            self.name = ""
            return
        aliases = ("name", "prefix")
        value = get_alias(data, aliases)
        if value:
            self.name = value
        elif not self.name:
            raise ValueError("Missing key 'volume.name'")

    def _check_label(self, data: dict):
        self.label = data.get("label", "")

    def _check_target(self, data: dict):
        aliases = ("target", "dest", "destination")
        value = get_alias(data, aliases)
        if not value:
            raise ValueError("Missing key 'volume.target'")
        self.target = value

    def _parse_domains(self, data: dict):
        self.domains = data.get("domains") or []

    def _parse_backup(self, data: dict):
        self.backup = data.get("backup") or {}

    def _parse_options(self, data: dict):
        self.options = data.get("option") or {}
