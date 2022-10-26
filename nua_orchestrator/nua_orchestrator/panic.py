"""Nua scripting: 'panic' and 'error' shortcuts."""

from .rich_console import print_red


def error(msg: str, status: int = 1):
    if not msg:
        msg = "unknown"
    if msg[-1] == ".":
        panic(f"Error: {msg.capitalize()}", status)
    else:
        panic(f"Error: {msg.capitalize()}.", status)


def panic(msg: str, status: int = 1):
    print_red(msg)
    raise SystemExit(status)
