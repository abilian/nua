from __future__ import annotations

from copy import deepcopy
from pprint import pformat

from nua.lib.console import print_red
from nua.lib.panic import error

from .utils import sanitized_name

# later, add 'npipe' when managed:
ALLOWED_TYPE = {"volume", "bind", "tmpfs"}
CHECKED_KEYS = {
    "_checked_",
    "dest",
    "destination",
    "domains",
    "driver",
    "options",
    "source_prefix",
    "source",
    "src_prefix",
    "src",
    "target",
    "type",
}


class Volume:
    """Representation of a volume attached to a container, either main
    container or Resource container."""

    def __init__(self):
        self._dict = {}

    def __str__(self) -> str:
        return pformat(self._dict)

    def __setitem__(self, key: int | str, item: Any):
        self._dict[key] = item

    def __getitem__(self, key: int | str) -> Any:
        return self._dict[key]

    def has_key(self, key: int | str) -> bool:
        return key in self._dict

    def get(self, key: int | str, default=None) -> Any:
        return self._dict.get(key, default)

    @classmethod
    def parse(cls, data: dict) -> Volume:
        """Parse a dict to obtain a Volume.

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
            self._check_source_prefix(data)
            self._check_source(data)
            self._check_target(data)
            self._parse_domains(data)
            self._parse_options(data)
            self._dict["_checked_"] = True
        except ValueError as e:
            print_red(str(e))
            print_red(pformat(data))
            error("Volume configuration has errors")

    @classmethod
    def normalize_list(cls, volume_list: list[dict]) -> list[dict]:
        """Parse each dict of the list to ensure it is valid volume.

        Return a list of valid volumes exported as dicts.
        """
        return [cls.parse(data).as_dict() for data in volume_list]

    @classmethod
    def update_name_dict(cls, data: dict, suffix: str) -> dict:
        volume = cls.parse(data)
        volume.update_name(suffix)
        return volume.as_dict()

    @classmethod
    def string(cls, data: dict) -> str:
        volume = cls.parse(data)
        lst = ["  "]
        lst.append(f"type={volume.type}")
        if volume.driver:
            lst.append(f"driver={volume.driver}")
        lst.append(f"source={volume.source}")
        if volume.domains:
            lst.append("\n   domains: " + ", ".join(volume.domains))
        return " ".join(lst)

    @classmethod
    def from_dict(cls, data: dict) -> "Volume":
        volume = cls()
        volume._dict = data
        return volume

    def as_dict(self) -> dict:
        return deepcopy(self._dict)

    @property
    def type(self) -> str:
        return self._dict.get("type", "")

    @type.setter
    def type(self, tpe: str):
        self._dict["type"] = tpe

    @property
    def driver(self) -> str:
        return self._dict.get("driver", "")

    @driver.setter
    def driver(self, driver: str):
        self._dict["driver"] = driver

    @property
    def prefix(self) -> str:
        return self._dict.get("source_prefix", "")

    @prefix.setter
    def prefix(self, source_prefix: str):
        self._dict["source_prefix"] = source_prefix

    @property
    def source(self) -> str:
        return self._dict.get("source", "")

    @source.setter
    def source(self, source: str):
        self._dict["source"] = source

    @property
    def target(self) -> str:
        return self._dict.get("target", "")

    @target.setter
    def target(self, target: str):
        self._dict["target"] = target

    @property
    def domains(self) -> list[str]:
        return self._dict.get("domains", [])

    @domains.setter
    def domains(self, domains: list[str]):
        self._dict["domains"] = domains

    @property
    def options(self) -> dict:
        return self._dict.get("options", {})

    @options.setter
    def options(self, options: dict):
        self._dict["options"] = options

    def update_name(self, suffix: str):
        if not (prefix := self.prefix):
            return
        self.source = sanitized_name(f"{prefix}-{suffix}")

    def _check_type(self, data: dict):
        tpe = data.get("type", "")
        if tpe not in ALLOWED_TYPE:
            raise ValueError("unknown value for 'volume.type'")
        self.type = tpe
        if tpe == "volume":
            self.driver = data.get("driver", "local")

    def _check_source_prefix(self, data: dict):
        if self.type == "tmpfs":
            # no source defined for "tmpfs" type
            return
        src_key = None
        for alias in ("source_prefix", "src_prefix"):
            if alias in data:
                src_key = alias
                break
        if not src_key:
            return
        value = data[src_key]
        if not value or not isinstance(value, str):
            raise ValueError("Invalid value for 'volume.source_prefix'")
        self.prefix = value

    def _check_source(self, data: dict):
        if self.type == "tmpfs":
            # no source for tmpfs
            return
        src_key = None
        for alias in ("source", "src"):
            if alias in data:
                src_key = alias
                break
        if src_key:
            value = data[src_key]
        else:
            if not self.prefix:
                raise ValueError("missing key 'volume.source'")
            value = ""
        if not (isinstance(value, str) and (value or self.prefix)):
            raise ValueError("Invalid value for 'volume.source'")
        self.source = value

    def _check_target(self, data: dict):
        dest_key = None
        for alias in ("target", "dest", "destination"):
            if alias in data:
                dest_key = alias
                break
        if not dest_key:
            raise ValueError("Missing key 'volume.target'")
        value = data[dest_key]
        if not value or not isinstance(value, str):
            raise ValueError("Invalid value for 'volume.target'")
        self.target = value

    def _parse_domains(self, data: dict):
        self.domains = data.get("domains", [])

    def _parse_options(self, data: dict):
        self.options = {k: v for k, v in data.items() if k not in CHECKED_KEYS}
        # mode = 'rw' is only at mount time
        if "mode" in self.options:
            del self.options["mode"]


######################
# def update_volume_name(volume: dict, suffix: str):
#     if "source_prefix" not in volume:
#         return
#     prefix = volume["source_prefix"]
#     volume["source"] = sanitized_name(f"{prefix}-{suffix}")
#
#
# def normalize_volumes(volume_list: list):
#     for volume in volume_list:
#         _normalize_volume(volume)
#
#
# def _normalize_volume(volume: dict):
#     try:
#         if not isinstance(volume, dict):
#             raise ValueError("'volume' must be a dict")
#         _check_type(volume)
#         if not _check_source_prefix(volume):
#             _check_source(volume)
#         _check_target(volume)
#     except ValueError as e:
#         print_red(str(e))
#         print_red(pformat(volume))
#         error("Volume configuration has errors")
#
#
# def _check_type(volume: dict):
#     if "type" not in volume:
#         volume["type"] = "volume"  # default value
#     if volume["type"] not in ALLOWED_TYPE:
#         raise ValueError("unknown value for 'volume.type'")
#     if volume["type"] == "volume" and "driver" not in volume:
#         # assuming default "local" driver
#         volume["driver"] = "local"
#
#
# def _check_source_prefix(volume: dict) -> bool:
#     if volume["type"] == "tmpfs":
#         # no source for tmpfs
#         return False
#     src_key = None
#     for alias in ("source_prefix", "src_prefix"):
#         if alias in volume:
#             src_key = alias
#             break
#     if not src_key:
#         return False
#     value = volume[src_key]
#     if not value or not isinstance(value, str):
#         raise ValueError("invalid value for 'volume.source_prefix'")
#     del volume[src_key]
#     volume["source_prefix"] = value
#     return True
#
#
# def _check_source(volume: dict):
#     if volume["type"] == "tmpfs":
#         # no source for tmpfs
#         return
#     src_key = None
#     for alias in ("source", "src"):
#         if alias in volume:
#             src_key = alias
#             break
#     if not src_key:
#         raise ValueError("missing key 'volume.source'")
#     value = volume[src_key]
#     if not value or not isinstance(value, str):
#         raise ValueError("invalid value for 'volume.source'")
#     del volume[src_key]
#     volume["source"] = value
#
#
# def _check_target(volume: dict):
#     dest_key = None
#     for alias in ("target", "dest", "destination"):
#         if alias in volume:
#             dest_key = alias
#             break
#     if not dest_key:
#         raise ValueError("missing key 'volume.target'")
#     value = volume[dest_key]
#     if not value or not isinstance(value, str):
#         raise ValueError("invalid value for 'volume.target'")
#     del volume[dest_key]
#     volume["target"] = value
