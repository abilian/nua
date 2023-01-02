import re
import string

from nua.lib.panic import error

RE_NB_UNIT = re.compile(r"(\d+\.?\d*)\s*(\S*)")
SIZE_UNIT = {"B": 1, "K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40}
RE_DURATION_UNIT = re.compile(r"(\d+\.?\d*)\s*(\S*)")
DURATION_UNIT = {"s": 1, "m": 60, "h": 3600, "d": 86400}
ALLOW_FIRST = set(string.ascii_lowercase + string.digits)
ALLOW_NAME = set(string.ascii_lowercase + string.digits + "_.-")


def image_size_repr(image_bytes: int, as_mib: bool) -> int:
    if as_mib:
        return round(image_bytes / 2**20)
    return round(image_bytes / 10**6)


def size_unit(as_mib: bool) -> str:
    if as_mib:
        return "MiB"
    return "MB"


def size_to_bytes(input: str) -> int:
    """Convert string representing size to bytes value.

    It uses basic regex to get results like: size_to_bytes("2k") 2048
    size_to_bytes("1MB") 1048576
    """
    if not input:
        return 0
    match = RE_NB_UNIT.search(input.strip())
    if not match or not match.group(1):
        return 0
    value = float(match.group(1))
    unit = match.group(2).upper()[0:1]
    return int(value * SIZE_UNIT.get(unit, 1))


def period_to_seconds(input: str) -> int:
    """Convert human-like time period to seconds value.

    It uses basic regex to get results like: period_to_seconds("1h")
    3600 period_to_seconds("24h") 86400
    """
    if not input:
        return 0
    match = RE_DURATION_UNIT.search(input.strip())
    if not match or not match.group(1):
        return 0
    value = float(match.group(1))
    unit = match.group(2).lower()[0:1]
    return int(value * DURATION_UNIT.get(unit, 1))


def sanitized_name(name: str, length=255) -> str:
    name = "".join(x for x in str(name).lower() if x in ALLOW_NAME)
    name = name[:length]
    if len(name) < 2:
        error(f"Name is too short: '{name}'")
    if name[0] not in ALLOW_FIRST:
        error(f"Name first character not valid: '{name}'")
    return name
