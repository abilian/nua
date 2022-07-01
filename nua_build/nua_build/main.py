"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nuad ..." for command line**.
See later if move this to "nua ...".
"""
from typing import Optional

import typer

from . import __version__
from .commands import build_cmd

state = {"verbose": False}

app = typer.Typer()

app.registered_commands += build_cmd.app.registered_commands


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


option_version = typer.Option(
    None,
    "--version",
    "-V",
    help="Show Nua version and exit.",
    callback=version_callback,
    is_eager=True,
)

option_verbose = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Write verbose output.",
)


def _version_string():
    typer.echo(f"Nua build CLI version: {__version__}")


def usage():
    _version_string()
    typer.echo("Usage: nuad [OPTIONS] COMMAND [ARGS]...\n\nTry 'nuad --help' for help.")
    raise typer.Exit(0)


def initialization():
    pass


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = option_version,
    verbose: bool = option_verbose,
):
    """Nua build CLI inferface."""
    initialization()
    if verbose:
        typer.echo("(Will write verbose output)")
        state["verbose"] = True
    if ctx.invoked_subcommand is None:
        usage()
