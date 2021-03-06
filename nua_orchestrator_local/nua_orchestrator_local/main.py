"""Script main entry point for Nua local."""
import sys
from typing import Optional

import typer

from . import __version__
from .actions import check_python_version

# setup_db() does create the db if needed and also populate the configuration
# from both db values and default parameters
from .db_setup import setup_db
from .exec import set_nua_user
from .local_cmd import status
from .rich_console import print_red

app = typer.Typer()
is_initialized = False


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
    typer.echo(f"Nua orchestrator local version: {__version__}")


def usage():
    _version_string()
    typer.echo(
        "Usage(wip): nua-orchestrator-local status\n"
        "Try 'nua-orchestrator-local --help' for help."
    )
    raise typer.Exit(0)


def initialization():
    global is_initialized

    if not check_python_version():
        print_red("Python 3.10+ is required for Nua orchestrator.")
        sys.exit(1)
    try:
        set_nua_user()
    except OSError:
        print_red("Nua orchestrator must be run as 'root' or 'nua'.")
        raise
    if is_initialized:
        return

    setup_db()
    is_initialized = True


@app.command("status")
def status_local():
    """Status of orchestrator."""
    initialization()
    status()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = option_version,
):
    """Nua orchestrator local."""
    initialization()
    if ctx.invoked_subcommand is None:
        usage()
