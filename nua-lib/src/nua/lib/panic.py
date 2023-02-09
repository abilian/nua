"""Nua scripting: print shortcuts."""
from typing import Any

from .console import (
    print_bold_yellow,
    print_bold_yellow_white,
    print_green,
    print_green_cyan,
    print_magenta,
    print_red,
    print_stream_blue,
)
from .tool.state import check_verbosity


def abort(msg: str, status: int = 1, explanation: str = ""):
    if not msg:
        msg = "unknown error"
    _print("Error", msg, explanation)
    if not status:
        status = 1
    raise SystemExit(status)


def warning(msg: str, explanation: str = ""):
    if check_verbosity():
        if not msg:
            msg = "unknown problem"
        _print("Warning", msg, explanation)


def _print(prefix: str, msg: str, explanation: str):
    print_red(f"{prefix}: {msg.capitalize()}")
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


def vprint(*args: Any):
    if check_verbosity():
        print(*args)


def vprint_blue(message: str):
    if check_verbosity():
        print_stream_blue(message)


def vprint_magenta(message: str):
    if check_verbosity():
        print_magenta(message)


def vprint_green(message: str):
    if check_verbosity():
        print_green(message)
