"""Nua scripting: print shortcuts.

All printing function should be encapsulated by a with verbosity(v) context for
future use in other message dispatching.


red bold: only for errors or serious warnings
    raise Abort()
    warning()  # got a Warning: prefix

red bold: warning lines
    red_line()

yellow bold: title of actions list
    title()
yellow bold + white: title of actions list
    title_info()

blue bold: when we’re about to start something important
    important()

green: when it’s done (i.e. for success messages)
    show()
green + cyan: information message with last part make visible
    info()

nocolor bold (default): : for normal immpotant messages (print)
    bold()

nocolor (default): for normal messages (print)
    vprint()  # with dependency on verbosity, so different from print
    vfprint() # and with stdout flush for rare special cases

magenta: for docker default log stream (without LF)
    print_stream()

gray: for debug messages (that are not supposed to be read, unless something goes
wrong or takes too much time)
    debug()

cyan: for emphasis in debug messages
    bold_debug()
"""
from typing import Any

from .console import (
    print_bold,
    print_bold_blue,
    print_bold_cyan,
    print_bold_red,
    print_bold_yellow,
    print_bold_yellow_white,
    print_cyan,
    print_green,
    print_green_cyan,
    print_magenta_no_lf,
)
from .tool.state import check_verbosity


class Abort(SystemExit):
    def __init__(
        self, msg: str = "unknown error", status: int = 1, explanation: str = ""
    ):
        if not msg:
            msg = "unknown error"
        _print_red_bold("Error", msg, explanation)
        super().__init__(status)


def warning(msg: str, explanation: str = ""):
    if check_verbosity():
        if not msg:
            msg = "unknown problem"
        _print_red_bold("Warning", msg, explanation)


def _print_red_bold(prefix: str, msg: str, explanation: str):
    if msg:
        msg = msg[0].upper() + msg[1:]
    print_bold_red(f"{prefix}: {msg}")
    if explanation:
        print_bold_red(f"    {explanation}")


def red_line(*args):
    if check_verbosity():
        print_bold_red(" ".join(str(x) for x in args))


def title(*args):
    if check_verbosity():
        print_bold_yellow(" ".join(str(x) for x in args))


def title_info(*args):
    if check_verbosity():
        print_bold_yellow_white(" ".join(str(x) for x in args))


def important(*args):
    if check_verbosity():
        print_bold_blue(" ".join(str(x) for x in args))


def show(*args: Any):
    if check_verbosity():
        print_green(" ".join(str(x) for x in args))


def info(*args: Any):
    if check_verbosity():
        print_green_cyan(" ".join(str(x) for x in args))


def bold(*args):
    if check_verbosity():
        print_bold(" ".join(str(x) for x in args))


def vprint(*args: Any):
    if check_verbosity():
        print(*args)


def vfprint(*args: Any):
    if check_verbosity():
        print(*args, end="", flush=True)


def print_stream(message: str):
    """Print Docker log stream already containing a LF."""
    if check_verbosity():
        print_magenta_no_lf(message)


def debug(*args: Any):
    if check_verbosity():
        print_cyan(" ".join(str(x) for x in args))


def bold_debug(*args: Any):
    if check_verbosity():
        print_bold_cyan(" ".join(str(x) for x in args))
