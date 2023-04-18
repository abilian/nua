"""Nua scripting: print shortcuts."""
from typing import Any

from .console import (
    print_blue,
    print_blue_bright_no_lf,
    print_bold_yellow,
    print_bold_yellow_white,
    print_green,
    print_green_cyan,
    print_magenta,
    print_red,
)
from .tool.state import check_verbosity


class Abort(SystemExit):
    def __init__(
        self, msg: str = "unknown error", status: int = 1, explanation: str = ""
    ):
        if not msg:
            msg = "unknown error"
        _print("Error", msg, explanation)
        super().__init__(status)


def warning(msg: str, explanation: str = ""):
    if check_verbosity():
        if not msg:
            msg = "unknown problem"
        _print("Warning", msg, explanation)


def _print(prefix: str, msg: str, explanation: str):
    if msg:
        msg = msg[0].upper() + msg[1:]
    print_red(f"{prefix}: {msg}")
    if explanation:
        print_red(f"    {explanation}")


def show(*args: Any):
    if check_verbosity():
        print_green(" ".join(str(x) for x in args))


def info(*args: Any):
    if check_verbosity():
        print_green_cyan(" ".join(str(x) for x in args))


def bold(*args):
    if check_verbosity():
        print_bold_yellow(" ".join(str(x) for x in args))


def title(*args):
    if check_verbosity():
        print_bold_yellow_white(" ".join(str(x) for x in args))


def print_log_stream(message: str):
    """Print log stream already containing a LF."""
    if check_verbosity():
        print_blue_bright_no_lf(message)


def vprint(*args: Any):
    if check_verbosity():
        print(*args)


def vfprint(*args: Any):
    if check_verbosity():
        print(*args, end="", flush=True)


def vprint_blue(message: str):
    if check_verbosity():
        print_blue(message)


def vprint_magenta(message: str):
    if check_verbosity():
        print_magenta(message)


def vprint_green(message: str):
    if check_verbosity():
        print_green(message)
