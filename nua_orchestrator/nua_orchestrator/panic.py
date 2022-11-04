"""Nua scripting: 'panic' and 'error' shortcuts."""

from .rich_console import print_red


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
