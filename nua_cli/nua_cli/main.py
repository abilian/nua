from typing import Optional

import typer

from . import __version__
from .commands import remote_load, server, users

app = typer.Typer()
app.add_typer(server.app, name="server")
app.add_typer(users.app, name="users")
app.add_typer(remote_load.app, name="remote")

state = {"verbose": False}


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
    typer.echo(f"Nua CLI version: {__version__}")


def usage():
    _version_string()
    typer.echo("Usage: nua [OPTIONS] COMMAND [ARGS]...\n\nTry 'nua --help' for help.")
    raise typer.Exit(0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = option_version,
    verbose: bool = option_verbose,
):
    """Nua CLI inferface."""
    if verbose:
        typer.echo("(Will write verbose output)")
        state["verbose"] = True
    if ctx.invoked_subcommand is None:
        usage()
