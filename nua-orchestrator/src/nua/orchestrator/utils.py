import importlib.util
import re
import string
from collections.abc import Callable, Iterable
from pathlib import Path

import tomli
import yaml
from nua.lib.panic import Abort

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


def size_to_bytes(size: str | None) -> int:
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
        raise Abort(f"Name is too short: '{name}'")
    if name[0] not in ALLOW_FIRST:
        # print("******")
        # import traceback
        # traceback.print_stack()
        raise Abort(f"Name first character not valid: '{name}'")
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


def load_module_function(package: str, module: str, function: str) -> Callable | None:
    spec = importlib.util.find_spec(f".{module}", package)
    if not spec:
        return None
    mod = spec.loader.load_module()
    if hasattr(mod, function):
        return getattr(mod, function)
    return None


def dehyphen(name: str) -> str:
    """Return stripped string with "-" changed to "_"."""
    return name.strip().replace("-", "_")


def hyphen(name: str) -> str:
    """Return stripped string with "_" changed to "-"."""
    return name.strip().replace("_", "-")


def hyphenized_set(data: Iterable[str]) -> set:
    return {hyphen(x) for x in data} | {dehyphen(x) for x in data}


def get_alias(data: dict, aliases: Iterable) -> str | None:
    for alias in aliases:
        if hyphen(alias) in data:
            return str(data[hyphen(alias)])
        if dehyphen(alias) in data:
            return str(data[dehyphen(alias)])
    return None
