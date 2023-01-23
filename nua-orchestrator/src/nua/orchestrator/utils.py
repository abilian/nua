import re
import string
from pathlib import Path

import tomli
import yaml
from nua.lib.panic import abort

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


def size_to_bytes(size: str) -> int:
    """Convert string representing size to bytes value.

    It uses basic regex to get results like: size_to_bytes("2k") 2048
    size_to_bytes("1MB") 1048576
    """
    if not size:
        return 0
    match = RE_NB_UNIT.search(size.strip())
    if not match or not match.group(1):
        return 0
    value = float(match.group(1))
    unit = match.group(2).upper()[0:1]
    return int(value * SIZE_UNIT.get(unit, 1))


def period_to_seconds(period: str) -> int:
    """Convert human-like time period to seconds value.

    It uses basic regex to get results like: period_to_seconds("1h")
    3600 period_to_seconds("24h") 86400
    """
    if not period:
        return 0
    match = RE_DURATION_UNIT.search(period.strip())
    if not match or not match.group(1):
        return 0
    value = float(match.group(1))
    unit = match.group(2).lower()[0:1]
    return int(value * DURATION_UNIT.get(unit, 1))


def sanitized_name(name: str, length=255) -> str:
    name = "".join(x for x in str(name).lower() if x in ALLOW_NAME)
    name = name[:length]
    if len(name) < 2:
        abort(f"Name is too short: '{name}'")
    if name[0] not in ALLOW_FIRST:
        abort(f"Name first character not valid: '{name}'")
    return name


def parse_any_format(path: Path) -> dict:
    """Parse the content of a file of type toml / json / yaml."""
    content = path.read_text(encoding="utf8")
    if path.suffix == ".toml":
        return tomli.loads(content)
    elif path.suffix in {".json", ".yaml", ".yml"}:
        return yaml.safe_load(content)
    else:
        raise ValueError(f"Unknown file extension for '{path}'")


def base20(value: int) -> str:
    """Display integer as base N."""
    chars = "bcdfghjklmnpqrstvwxz"
    if value < 0:
        raise ValueError("Value must be positive")
    b20 = []
    while True:
        value, remain = divmod(value, len(chars))
        b20.append(remain)
        if not value:
            break
    b20.reverse()
    return "".join(chars[x] for x in b20)
