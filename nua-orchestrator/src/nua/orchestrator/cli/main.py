"""Script main entry point for Nua local."""
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from nua.lib.panic import warning
from nua.lib.tool.state import set_color, set_verbosity

from .. import __version__
from ..search_cmd import search_nua_print
from . import configuration as config_cmd
from . import debug
from .commands.api import API
from .commands.backup import backup_all
from .commands.deploy_remove import (
    deploy_merge_nua_app,
    deploy_nua_apps,
    remove_nua_domain,
)
from .commands.restore import restore_nua_apps_replay, restore_nua_apps_strict
from .commands.start_stop import (
    restart_nua_instance_domain,
    start_nua_instance_domain,
    stop_nua_instance_domain,
)
from .commands.status import status
from .init import initialization

ALLOW_SUFFIX = {".json", ".toml", ".yaml", ".yml"}

app = typer.Typer()
app.add_typer(config_cmd.app, name="config", no_args_is_help=True)
app.add_typer(debug.app, name="debug", no_args_is_help=True)

arg_search_app = typer.Argument(..., help="App id or image name.")
arg_deploy_app = typer.Argument(
    ..., metavar="APP", help="App config file (json or toml file)."
)


def version_callback(value: bool) -> None:
    if value:
        _print_version()
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
option_json = typer.Option(False, "--json", help="Output result as JSON.")
option_short = typer.Option(False, help="Show short text result.")
option_raw = typer.Option(False, "--raw", help="Return raw result (not JSON).")
option_domain = typer.Option("", "--domain", "-d", help="Select domain to stop.")


def _print_version():
    typer.echo(f"Nua orchestrator local version: {__version__}")


def usage():
    _print_version()
    typer.echo("Usage(wip): nua status\n" "Try 'nua --help' for help.")
    raise typer.Exit(0)


@app.command("status")
def status_local():
    """Status of orchestrator."""
    initialization()
    set_verbosity(1)
    status()


@app.command("reload")
def reload_local():
    """Rebuild config and restart apps."""
    print("Not implemented yet.")
    initialization()
    # TODO (not implemented yet)
    # reload_servers()


@app.command("search")
def search_local(app: str = arg_search_app):
    """Search Nua image."""
    initialization()
    search_nua_print(app)


@app.command("deploy")
def deploy_local(
    apps_conf: str = arg_deploy_app,
    verbose: int = opt_verbose,
    colorize: bool = option_color,
):
    """Deploy one or several Nua applications."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()

    path = Path(apps_conf)
    if path.suffix in ALLOW_SUFFIX and path.is_file():
        deploy_merge_nua_app(apps_conf)
    else:
        warning("Unknown file format.")


@app.command("deploy-replace")
def deploy_replace_local(
    apps_conf: str = arg_deploy_app,
    verbose: int = opt_verbose,
    colorize: bool = option_color,
):
    """Replace all deployed instances by new deployment list."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()

    path = Path(apps_conf)
    if path.suffix in ALLOW_SUFFIX and path.is_file():
        deploy_nua_apps(apps_conf)
    else:
        warning("Unknown file format.")


@app.command("remove")
def remove_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    domain: str = option_domain,
):
    """Remove a deployed instance and all its data."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if domain:
        remove_nua_domain(domain)
    else:
        print("WIP: currently a domain must be provided.")


@app.command("restore")
def restore_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    strict: bool = option_restore_strict,
):
    """Restore last successful deployment."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if strict:
        restore_nua_apps_strict()
    else:
        restore_nua_apps_replay()


@app.command("stop")
def stop_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    domain: str = option_domain,
):
    """Stop a deployed instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if domain:
        stop_nua_instance_domain(domain)
    else:
        print("WIP: currently a domain must be provided.")


@app.command("start")
def start_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    domain: str = option_domain,
):
    """Start a deployed instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if domain:
        start_nua_instance_domain(domain)
    else:
        print("WIP: currently a domain must be provided.")


@app.command("restart")
def restart_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    domain: str = option_domain,
):
    """Restart a deployed instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if domain:
        restart_nua_instance_domain(domain)
    else:
        print("WIP: currently a domain must be provided.")


@app.command("backup")
def backup_all_cmd(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
):
    """Backup now all instance having a backup rules."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    backup_all()


@app.command("rpc", hidden=True)
def rpc(method: str, raw: bool = option_raw):
    """RPC call (used by nua-cli)."""
    initialization()
    api = API()
    args_str = sys.stdin.read()
    if not args_str:
        args = {}
    else:
        args = json.loads(args_str)
    result = api.call(method, **args)
    if raw:
        print(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = opt_version,
):
    """Nua orchestrator local."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
