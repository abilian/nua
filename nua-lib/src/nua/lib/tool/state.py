import os

STATE = {"verbose": 0, "colorize": True}


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


def verbosity(threshold: int = 1) -> bool:
    return STATE["verbose"] >= threshold


def use_color() -> bool:
    if "NO_COLOR" in os.environ:
        return False
    return bool(STATE["colorize"])  # noqa
