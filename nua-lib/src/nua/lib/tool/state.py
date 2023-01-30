import os
from contextlib import contextmanager

STATE = {"verbose": 0, "colorize": True, "verbose_threshold": -1}


def set_verbosity(value: int):
    STATE["verbose"] = value


def verbosity_level() -> int:
    return STATE["verbose"]


def set_color(flag: bool):
    STATE["colorize"] = flag
    if flag:
        os.environ.pop("NO_COLOR", None)
    else:
        os.environ["NO_COLOR"] = "1"


def use_color() -> bool:
    if "NO_COLOR" in os.environ:
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
