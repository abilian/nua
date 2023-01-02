from __future__ import annotations

import typer

from nua.cli.version import get_version


def _version_callback(value: bool) -> None:
    if value:
        _print_version()
        raise typer.Exit(0)


OPTS = {
    "version": typer.Option(
        None,
        "--version",
        "-V",
        help="Show Nua version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    "verbose": typer.Option(
        0, "--verbose", "-v", help="Show more informations, until -vvv.", count=True
    ),
    "color": typer.Option(True, "--color/--no-color", help="Colorize messages."),
}


def _print_version():
    typer.echo(f"Nua CLI version: {get_version()}")
