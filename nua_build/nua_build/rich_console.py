"""Define console (singleton)"""
import rich.console

console = rich.console.Console()


def print_green(msg: str):
    console.print(msg, style="green")


def print_magenta(msg: str):
    console.print(msg, style="magenta")


def print_red(msg: str):
    console.print(msg, style="bold red")
