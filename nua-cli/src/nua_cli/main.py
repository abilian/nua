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
[x] logs              Tail running logs
[ ] restart           Restart an app
[ ] run               Run a command in the app's environment
[ ] scale             Scale processes
[ ] server            Manage the Nua server
[ ] start             Start an app
[ ] status            Show app status
[ ] stop              Stop an app
[ ] update            Update an app
[x] version           Show Nua version
"""
from __future__ import annotations

import subprocess
from typing import Optional

import snoop
import typer

from .client import get_client
from .commands import config, server
from .common import OPTS, get_current_app_id
from .version import get_version

snoop.install()

cli = typer.Typer()
client = get_client()


# Subcommands
cli.add_typer(server.cli)
cli.add_typer(config.cli)


#
# Done
#
@cli.command()
def apps():
    """List applications."""
    result = client.call("list")
    for instance in result:
        app_id = instance["app_id"]
        container_id = instance["site_config"]["container_id"]
        container_info = client.get_container_info(container_id)
        status = container_info[0]["State"]["Status"]
        match status:
            case "running":
                color = typer.colors.GREEN
            case "exited":
                color = typer.colors.RED
            case _:
                color = typer.colors.YELLOW
        typer.secho(f"{app_id} ({status})", fg=color)


@cli.command()
def help(ctx: typer.Context):
    """Show help."""
    print(ctx.get_help())


@cli.command()
def version():
    """Show Nua version."""
    typer.echo(f"Nua CLI version: {get_version()}")
    status = client.call("status")
    typer.echo(f"Nua Server version: {status['version']}")


@cli.command()
def backup():
    """Backup a deployed application."""
    result = client.call_raw("backup")
    print(result)


#
# TODO: application lifecycle operations
#
@cli.command()
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


@cli.command()
def destroy():
    """Destroy an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@cli.command()
def start():
    """Start an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@cli.command()
def stop():
    """Stop an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@cli.command()
def logs(app_id: Optional[str] = typer.Argument(None, help="Application ID")):
    """Show application logs."""
    # Quick & dirty implementation that calls docker directly.
    if not app_id:
        app_id = get_current_app_id()
    app_info = client.get_app_info(app_id)
    container_id = app_info["site_config"]["container_id"]
    result = client.ssh(f"docker logs {container_id}")
    # Note: 'docker logs' returns data to both stderr and stdout.
    # We need to merge the two streams, on find another way
    print(result.stderr)


@cli.command()
def update():
    """Update an application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@cli.command()
def restore():
    """Restore backup data of a deployed application."""
    typer.secho("Not implemented yet", fg=typer.colors.RED)


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = OPTS["version"],
):
    """Nua CLI."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
