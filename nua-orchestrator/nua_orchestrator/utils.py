import re
import string

from .common.panic import error

RE_NB_UNIT = re.compile(r"(\d+\.?\d*)\s*(\S*)")
UNIT = {"B": 1, "K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40}
ALLOW_FIRST = set(string.ascii_lowercase + string.digits)
ALLOW_NAME = set(string.ascii_lowercase + string.digits + "_.-")


def image_size_repr(image_bytes: int, as_mib: bool) -> int:
    if as_mib:
        return round(image_bytes / 2**20)
    return round(image_bytes / 10**6)


def size_unit(as_mib: bool) -> str:
    return "MiB" if as_mib else "MB"


def size_to_bytes(input: str) -> int:
    """Convert string representing size to bytes value."""
    if not input:
        return 0
    match = RE_NB_UNIT.search(input.strip())
    if not match or not match.group(1):
        return 0
    value = float(match.group(1))
    unit = match.group(2).upper()[0:1]
    return int(value * UNIT.get(unit, 1))


def sanitized_name(name: str, length=255) -> str:
    name = "".join(x for x in str(name).lower() if x in ALLOW_NAME)
    name = name[:length]
    if len(name) < 2:
        error(f"Name is too short: '{name}'")
    if name[0] not in ALLOW_FIRST:
        error(f"Name first character not valid: '{name}'")
    return name
