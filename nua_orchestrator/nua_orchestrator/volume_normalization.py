from pprint import pformat

from .panic import error
from .rich_console import print_red

# later, add 'npipe' when managed:
ALLOWED_TYPE = {"volume", "bind", "tmpfs"}


def normalize_volumes(volume_list: list):
    for volume in volume_list:
        _normalize_volume(volume)


def _normalize_volume(volume: dict):
    try:
        if not isinstance(volume, dict):
            raise ValueError("'volume' must be a dict")
        _check_type(volume)
        _check_source(volume)
        _check_target(volume)
    except ValueError as e:
        print_red(str(e))
        print_red(pformat(volume))
        error("Volume configuration has errors")


def _check_type(volume: dict):
    if "type" not in volume:
        volume["type"] = "volume"  # default value
    if volume["type"] not in ALLOWED_TYPE:
        raise ValueError("unknown value for 'volume.type'")
    if volume["type"] == "volume" and "driver" not in volume:
        # assuming default "local" driver
        volume["driver"] = "local"


def _check_source(volume: dict):
    if volume["type"] == "tmpfs":
        # no source for tmpfs
        return
    src_key = None
    for alias in ("source", "src"):
        if alias in volume:
            src_key = alias
            break
    if not src_key:
        raise ValueError("missing key 'volume.source'")
    value = volume[src_key]
    if not value or not isinstance(value, str):
        raise ValueError("invalid value for 'volume.source'")
    del volume[src_key]
    volume["source"] = value


def _check_target(volume: dict):
    dest_key = None
    for alias in ("target", "dest", "destination"):
        if alias in volume:
            dest_key = alias
            break
    if not dest_key:
        raise ValueError("missing key 'volume.target'")
    value = volume[dest_key]
    if not value or not isinstance(value, str):
        raise ValueError("invalid value for 'volume.target'")
    del volume[dest_key]
    volume["target"] = value
