from __future__ import annotations

import json
from typing import Optional

import typer

from nua.cli.client import Client
from nua.cli.common import OPTS, print_version

# FIXME: this assume a particular layout of ~nua account on the server,
NUA_CMD = "./nua310/bin/nua-orchestrator"

app = typer.Typer()


def _usage():
    print_version()
    typer.echo("Usage(wip): nua status\n" "Try 'nua --help' for help.")
    raise typer.Exit(0)


@app.command()
def deploy():
    """Deploy an application."""


@app.command()
def list():
    """List applications."""
    client = Client()
    r = client.run(f"{NUA_CMD} list-instances --json")
    for instance in json.loads(r.stdout):
        typer.echo(instance["app_id"])


@app.command()
def destroy():
    """Destroy an application."""


@app.command()
def start():
    """Start an application."""


@app.command()
def stop():
    """Stop an application."""


@app.command()
def help():
    """Show help."""
    _usage()


@app.command()
def version():
    """Show version."""
    print_version()


@app.command()
def status():
    """Show Nua status."""
    client = Client()
    r = client.run(f"{NUA_CMD} status")
    msg = f"Ran {r.command!r} on {r.connection.host}, got stdout:\n\n{r.stdout}"
    print(msg)


@app.command()
def logs():
    """Show application logs."""


@app.command()
def config():
    """Show application config."""


@app.command()
def update():
    """Update an application."""


@app.command()
def backup():
    """Backup a deployed application."""


@app.command()
def restore():
    """Restore backup data of a deployed application."""


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
