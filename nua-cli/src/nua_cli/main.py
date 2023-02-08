"""
TODO:

apps              List apps
build             Build app but don't deploy it
backup            Backup/restore app data
config            Show/manage config for current app
deploy            Deploy app
destroy           Destroy app
help              Display help
init              Create a new app
logs              Tail running logs
ps                Show process count
restart           Restart an app
run               Run a command in the app's environment
scale             Scale processes
settings          Show server settings
start             Start an app
status            Show app status
stop              Stop an app
update            Update the Nua CLI
"""
from __future__ import annotations

import subprocess
from typing import Optional

import snoop
import typer
from snoop import pp

from nua_cli.version import get_version

from .client import get_client
from .common import OPTS, print_version
from .subcommands import config, server

snoop.install()
app = typer.Typer()
client = get_client()


# Subcommands
app.add_typer(server.app, name="server", help="Manage the Nua server")
app.add_typer(config.app, name="config", help="Show / edit app config")


def _usage():
    print_version()
    typer.echo("Usage(wip): nua status\n" "Try 'nua --help' for help.")
    raise typer.Exit(0)


#
# Done
#
@app.command()
def apps():
    """List applications."""
    result = client.call("list")
    for instance in result:
        typer.echo(instance["app_id"])


@app.command()
def help():
    """Show help."""
    _usage()


@app.command()
def version():
    """Show Nua version."""
    typer.echo(f"Nua CLI version: {get_version()}")
    status = client.call("status")
    typer.echo(f"Nua Server version: {status['version']}")


@app.command()
def backup():
    """Backup a deployed application."""
    result = client.call_raw("backup")
    print(result)


#
# TODO: application lifecycle operations
#
@app.command()
def build(path: str = "."):
    """Build app but don't deploy it."""

    subprocess.run(["nua-dev", "build", path])


@app.command()
def deploy(imagename: str, domainname: str):
    """Deploy an application."""
    deply_config = {
        "site": [
            {
                "domain": domainname,
                "image": imagename,
            },
        ],
    }
    result = client.call("deploy", deploy_config=deply_config)
    pp(result)


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
def logs():
    """Show application logs."""


@app.command()
def update():
    """Update an application."""


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
