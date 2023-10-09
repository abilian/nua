from functools import wraps

from .tool.color_str import ColorStr
from .tool.state import use_color


def if_color(func):
    @wraps(func)
    def wrapper(*args):
        if use_color():
            return func(*args)
        else:
            return print(*args)

    return wrapper


@if_color
def print_green(msg: str):
    print(ColorStr.green(msg))


@if_color
def print_gray(msg: str):
    print(ColorStr.gray(msg))


@if_color
def print_blue(msg: str):
    print(ColorStr.blue(msg))


@if_color
def print_bold_blue(msg: str):
    print(ColorStr.blue_bold(msg))


@if_color
def print_magenta(msg: str):
    print(ColorStr.magenta(msg))


@if_color
def print_red(msg: str):
    print(ColorStr.red(msg))


@if_color
def print_bold_red(msg: str):
    print(ColorStr.red_bold(msg))


@if_color
def print_bold(msg: str):
    print(ColorStr.colorize(msg, bold=True))


@if_color
def print_bold_yellow(msg: str):
    print(ColorStr.yellow_bold(msg))


@if_color
def print_cyan(msg: str):
    print(ColorStr.cyan(msg))


@if_color
def print_bold_cyan(msg: str):
    print(ColorStr.cyan_bold(msg))


@if_color
def print_bold_yellow_white(msg: str):
    parts = msg.rsplit(" ", 1)
    if len(parts) == 2:
        print(ColorStr.yellow_bold(parts[0]), ColorStr.white_bold(parts[1]))
    else:
        print(ColorStr.yellow_bold(msg))


@if_color
def print_green_cyan(msg: str):
    parts = msg.rsplit(" ", 1)
    if len(parts) == 2:
        print(ColorStr.green(parts[0]), ColorStr.cyan(parts[1]))
    else:
        print(ColorStr.green(msg))


@if_color
def print_magenta_no_lf(msg: str):
    """Print specialized for lines including a LF (Docker build log)."""
    print(ColorStr.magenta(msg), end="")
