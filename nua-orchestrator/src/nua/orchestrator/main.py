"""Script main entry point for Nua local."""
import os
from pathlib import Path
from pprint import pformat
from typing import Optional

import typer
from nua.lib.actions import check_python_version
from nua.lib.console import print_red
from nua.lib.exec import is_current_user, set_nua_user
from nua.lib.panic import error
from nua.lib.tool.state import set_color, set_verbose

from . import __version__
from .commands.deploy import deploy_nua_sites
from .commands.deploy_nua import deploy_nua
from .commands.restore import restore_nua_sites_replay, restore_nua_sites_strict
from .db.store import installed_nua_settings, list_all_settings

# setup_db() does create the db if needed and also populate the configuration
# from both db values and default parameters
from .db_setup import setup_db
from .local_cmd import reload_servers, status
from .search_cmd import search_nua_print

app = typer.Typer()
is_initialized = False
arg_search_app = typer.Argument(..., help="App id or image name.")
arg_deploy_app = typer.Argument(
    ..., metavar="APP", help="App id or image name (or toml file)."
)


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


opt_version = typer.Option(
    None,
    "--version",
    "-V",
    help="Show Nua version and exit.",
    callback=version_callback,
    is_eager=True,
)
opt_verbose = typer.Option(
    0, "--verbose", "-v", help="Show more informations, until -vvv.", count=True
)
option_color = typer.Option(True, "--color/--no-color", help="Colorize messages.")
option_restore_strict = typer.Option(
    False, "--strict/--replay", help="Use strict restore mode."
)


def _version_string():
    typer.echo(f"Nua orchestrator local version: {__version__}")


def usage():
    _version_string()
    typer.echo("Usage(wip): nua status\n" "Try 'nua --help' for help.")
    raise typer.Exit(0)


def initialization():
    global is_initialized

    if not check_python_version():
        error("Python 3.10+ is required for Nua orchestrator.")
    if os.getuid() == 0 or is_current_user("nua"):
        set_nua_user()
    else:
        print_red("Nua orchestrator must be run as 'root' or 'nua'.")
        raise typer.Exit(1)
    if is_initialized:
        return
    setup_db()
    is_initialized = True


@app.command("status")
def status_local():
    """Status of orchestrator."""
    initialization()
    status()


@app.command("reload")
def restart_local():
    """Rebuild config and restart apps."""
    initialization()
    reload_servers()


@app.command("search")
def search_local(app: str = arg_search_app):
    """Search Nua image."""
    initialization()
    search_nua_print(app)


@app.command("deploy")
def deploy_local(
    app_name: str = arg_deploy_app,
    verbose: int = opt_verbose,
    colorize: bool = option_color,
):
    """Search, install and launch Nua image."""
    set_verbose(verbose)
    set_color(colorize)
    if app_name.endswith(".toml") and Path(app_name).is_file():
        initialization()
        deploy_nua_sites(app_name)
    else:
        initialization()
        deploy_nua(app_name)


@app.command("restore")
def restore_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    strict: bool = option_restore_strict,
):
    """Restore last successful deployment."""
    set_verbose(verbose)
    set_color(colorize)
    initialization()
    if strict:
        restore_nua_sites_strict()
    else:
        restore_nua_sites_replay()


@app.command("show_db_settings")
def show_db_settings():
    """Debug: show settings in db."""
    initialization()
    print(pformat(list_all_settings()))


@app.command("show_nua_settings")
def show_nua_settings():
    """Debug: show Nua orchestrator settings in db."""
    initialization()
    print(pformat(installed_nua_settings()))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = opt_version,
):
    """Nua orchestrator local."""
    initialization()
    if ctx.invoked_subcommand is None:
        usage()
