"""Script to launch the server of the orchestrator."""
from typing import Optional

import typer

from . import __version__

# setup_db() does create the db if needed and also populate the configuration
# from both db values and default parameters
from .db_setup import setup_db  # and also populate config
from .server import restart, start, status, stop

# state = {"verbose": False}

app = typer.Typer()

# app.add_typer(
#     settings_cmd.app,
#     name="settings",
#     help="Settings management (show or load settings).",
# )


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


def _version_string():
    typer.echo(f"Nua orchestrator server version: {__version__}")


def usage():
    _version_string()
    typer.echo(
        "Usage: nua-orchestrator [start|status|restart|stop]\nTry 'nua-orchestrator --help' for help."
    )
    raise typer.Exit(0)


def initialization():
    setup_db()


@app.command("start")
def start_server():
    """Start orchestrator server."""
    start()


@app.command("restart")
def restart_server():
    """Restart orchestrator server."""
    restart()


@app.command("status")
def status_server():
    """Status of orchestrator server."""
    status()


@app.command("stop")
def stop_server():
    """Stop orchestrator server."""
    stop()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = option_version,
):
    """Nua orchestrator server."""
    initialization()
    if ctx.invoked_subcommand is None:
        usage()
