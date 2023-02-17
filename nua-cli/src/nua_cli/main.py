"""
TODO:

[x] = done
[ ] = not done

[x] apps              List apps
[x] build             Build app but don't deploy it
[x] backup            Backup/restore app data
[x] config            Show/manage config for current app
[ ] deploy            Deploy app
[ ] destroy           Destroy app
[ ] help              Display help
[ ] init              Create a new app
[ ] logs              Tail running logs
[ ] ps                Show process count
[ ] restart           Restart an app
[ ] run               Run a command in the app's environment
[ ] scale             Scale processes
[ ] settings          Show server settings
[ ] start             Start an app
[ ] status            Show app status
[ ] stop              Stop an app
[ ] update            Update the Nua CLI
[x] version           Show Nua version
"""
from __future__ import annotations

import subprocess
from pprint import pp
from typing import Optional

import typer

from nua_cli.version import get_version

from .client import get_client
from .common import OPTS
from .subcommands import config, server

app = typer.Typer()
client = get_client()


# Subcommands
app.add_typer(server.app)
app.add_typer(config.app)


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
def help(ctx: typer.Context):
    """Show help."""
    print(app)


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
def build(
    path: str = ".",
    experimental: bool = typer.Option(
        False, "--experimental", "-x", help="Use experimental builder (from nua-dev)."
    ),
    verbose: int = typer.Option(
        0, "--verbose", "-v", help="Increase verbosity level, until -vv. ", count=True
    ),
    quiet: int = typer.Option(
        0, "--quiet", "-q", help="Decrease verbosity level", count=True
    ),
):
    """Build app but don't deploy it."""

    verbosity = 1 + verbose - quiet
    verbosity_flags = verbosity * ["-v"]

    if experimental:
        typer.secho(
            "Using experimental builder (from nua-dev).", fg=typer.colors.YELLOW
        )
        subprocess.run(["nua-dev", "build", path])
    else:
        subprocess.run(["nua-build"] + verbosity_flags + [path])


@app.command()
def deploy(image: str, domain: str):
    """Deploy an application."""
    deply_config = {
        "site": [
            {
                "domain": domain,
                "image": image,
            },
        ],
    }
    result = client.call("deploy", deploy_config=deply_config)
    pp(result)


@app.command()
def destroy():
    """Destroy an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@app.command()
def start():
    """Start an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@app.command()
def stop():
    """Stop an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@app.command()
def logs():
    """Show application logs."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@app.command()
def update():
    """Update an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@app.command()
def restore():
    """Restore backup data of a deployed application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = OPTS["version"],
):
    """Nua CLI."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
