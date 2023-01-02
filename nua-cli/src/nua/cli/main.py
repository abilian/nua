from __future__ import annotations

from typing import Optional

import typer

from nua.cli.client import Client
from nua.cli.common import OPTS, _print_version

NUA_CMD = "./bin/nua"

app = typer.Typer()


def _usage():
    _print_version()
    typer.echo("Usage(wip): nua status\n" "Try 'nua --help' for help.")
    raise typer.Exit(0)


@app.command()
def version():
    """Show Nua version and exit."""
    _print_version()


@app.command()
def help():
    """Show help."""
    _usage()


@app.command()
def status():
    """Show Nua status."""
    client = Client()
    r = client.run('bin/nua status')
    msg = f"Ran {r.command!r} on {r.connection.host}, got stdout:\n\n{r.stdout}"
    print(msg)


@app.command()
def deploy():
    """Deploy an application."""


@app.command()
def list():
    """List applications."""


@app.command()
def destroy():
    """Destroy an application."""


@app.command()
def logs():
    """Show application logs."""


@app.command()
def config():
    """Show application config."""


@app.command()
def init():
    """Initialize a new application."""


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = OPTS["version"],
):
    """Nua local CLI."""
    # initialization()
    if ctx.invoked_subcommand is None:
        _usage()


if __name__ == "__main__":
    app()
