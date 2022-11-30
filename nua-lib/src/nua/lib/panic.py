"""Nua scripting: 'panic' and 'error' shortcuts."""
from typing import Any

from .rich_console import (  # print_bold,
    print_bold_yellow,
    print_bold_yellow_white,
    print_green,
    print_green_cyan,
    print_red,
)


def error(msg: str, status: int = 1, explanation: str = ""):
    if not msg:
        msg = "unknown error"
    _print("Error", msg, explanation)
    if not status:
        status = 1
    raise SystemExit(status)


def warning(msg: str, explanation: str = ""):
    if not msg:
        msg = "unknown problem"
    _print("Warning", msg, explanation)


def _print(prefix: str, msg: str, explanation: str):
    if msg[-1] == ".":
        print_red(f"{prefix}: {msg.capitalize()}")
    else:
        print_red(f"{prefix}: {msg.capitalize()}.")
    if explanation:
        print_red(f"    {explanation}")


def show(*args: Any):
    print_green(" ".join(str(x) for x in args))


def info(*args: Any):
    print_green_cyan(" ".join(str(x) for x in args))


def bold(*args):
    print_bold_yellow(" ".join(str(x) for x in args))


def title(*args):
    print_bold_yellow_white(" ".join(str(x) for x in args))
