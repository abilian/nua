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
from operator import itemgetter
from typing import Optional

import snoop
import typer
from snoop import pp

from nua_cli.version import get_version

from .client import Client
from .common import OPTS, print_version

snoop.install()
app = typer.Typer()
client = Client()


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
def settings():
    """Show server settings."""
    result = client.call("settings")
    pp(result)


@app.command()
def status():
    """Show Nua status."""
    result = client.call("status")

    print(f"Nua version: {result['version']}")

    registries = result["registries"]
    print("Configured registries:")
    for reg in sorted(registries, key=itemgetter("priority")):
        msg = (
            f'  priority: {reg["priority"]:>2}   '
            f'format: {reg["format"]:<16}   '
            f'url: {reg["url"]}'
        )
        print(msg)


@app.command()
def list():
    """List applications (alias for `apps` - which one do we keep?)."""
    apps()


@app.command()
def help():
    """Show help."""
    _usage()


@app.command()
def version():
    """Show version."""
    typer.echo(f"Nua CLI version: {get_version()}")
    status = client.call("status")
    typer.echo(f"Nua Server version: {status['version']}")


@app.command()
def server_log():
    """Show server logs (TODO: rename as subcommand?) (TODO: not working)."""
    result = client.call_raw("server_log")
    print(result)
    # typer.echo(result)


@app.command()
def backup():
    """Backup a deployed application."""
    result = client.call_raw("backup")
    print(result)


#
# TODO
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
def config():
    """Show application config."""


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
