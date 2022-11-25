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
def print_magenta(msg: str):
    print(ColorStr.magenta(msg))


@if_color
def print_red(msg: str):
    print(ColorStr.red_bold(msg))


@if_color
def print_bold(msg: str):
    print(ColorStr.colorize(msg, bold=True))


@if_color
def print_bold_yellow(msg: str):
    print(ColorStr.yellow_bold(msg))
