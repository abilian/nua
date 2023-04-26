import os
from contextlib import contextmanager
from functools import cache
from pathlib import Path

STATE = {
    "verbose": 0,
    "colorize": True,
    "verbose_threshold": -1,
    "packages_updated": False,
}


def set_verbosity(value: int):
    assert isinstance(value, int)
    STATE["verbose"] = value


def verbosity_level() -> int:
    return STATE["verbose"]


def set_color(flag: bool):
    assert isinstance(flag, bool)
    STATE["colorize"] = flag
    if flag:
        os.environ.pop("NO_COLOR", None)
    else:
        os.environ["NO_COLOR"] = "1"


def use_color() -> bool:
    if "NO_COLOR" in os.environ or is_inside_container():
        return False
    return bool(STATE["colorize"])  # noqa


@contextmanager
def verbosity(level: int):
    previous = STATE["verbose_threshold"]
    STATE["verbose_threshold"] = level
    try:
        yield
    finally:
        STATE["verbose_threshold"] = previous


def check_verbosity() -> bool:
    return STATE["verbose"] >= STATE["verbose_threshold"]


@cache
def is_inside_container() -> bool:
    """Test if current execution environment is inside a container."""
    try:
        return Path("/nua/metadata/nua-config.json").is_file()
    except PermissionError:
        return False


def set_packages_updated(flag: bool) -> None:
    STATE["packages_updated"] = flag


def packages_updated() -> bool:
    return bool(STATE.get("packages_updated", False))
