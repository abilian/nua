"""Script main entry point for Nua local."""
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from nua.lib.panic import warning
from nua.lib.tool.state import set_color, set_verbosity

from .. import __version__
from ..api import API
from ..init import initialization
from ..search_cmd import search_nua_print
from . import configuration as config_cmd
from . import debug
from .commands.backup_restore import (
    backup_all_apps,
    backup_one_app,
    restore_last_backup,
    restore_list_backups,
)
from .commands.deploy_remove import (
    deploy_merge_nua_app,
    deploy_nua_apps,
    remove_nua_domain,
    remove_nua_label,
)
from .commands.restore_deployed import restore_active_state
from .commands.start_stop import (
    restart_nua_instance,
    start_nua_instance,
    stop_nua_instance,
)
from .commands.status import StatusCommand

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
option_json = typer.Option(False, "--json", help="Output result as JSON.")
option_short = typer.Option(False, help="Show short text result.")
option_raw = typer.Option(False, "--raw", help="Return raw result (not JSON).")
option_all_apps = typer.Option(False, "--all", "-a", help="Select all apps.")
option_label = typer.Option("", "--label", "-l", help="Select app by label.")
option_domain = typer.Option("", "--domain", "-d", help="Select app by domain.")
option_list_backup = typer.Option(False, "--list", help="List available backups.")
option_last_backup = typer.Option(
    False, "--last", help="Restore from last available backup."
)


def _print_version():
    typer.echo(f"Nua orchestrator local version: {__version__}")


def usage():
    _print_version()
    typer.echo("Usage(wip): nua status\n" "Try 'nua --help' for help.")
    raise typer.Exit(0)


@app.command("status")
def status_local() -> None:
    """Status of orchestrator."""
    initialization()
    set_verbosity(0)
    status = StatusCommand()
    status.display()


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
    label: str = option_label,
    domain: str = option_domain,
):
    """Remove a deployed instance and all its data."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if label:
        remove_nua_label(label)
    elif domain:
        remove_nua_domain(domain)
    else:
        print("WIP: currently a label or domain must be provided.")


@app.command("restore-deployed")
def restore_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
):
    """Restore last successful deployment."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    restore_active_state()


@app.command("stop")
def stop_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    label: str = option_label,
    domain: str = option_domain,
):
    """Stop a deployed instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if label:
        stop_nua_instance(label=label)
    elif domain:
        stop_nua_instance(domain=domain)
    else:
        print("WIP: currently a label or domain must be provided.")


@app.command("start")
def start_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    label: str = option_label,
    domain: str = option_domain,
):
    """Start a deployed instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if label:
        start_nua_instance(label=label)
    elif domain:
        start_nua_instance(domain=domain)
    else:
        print("WIP: currently a label or domain must be provided.")


@app.command("restart")
def restart_local(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    label: str = option_label,
    domain: str = option_domain,
):
    """Restart a deployed instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if label:
        restart_nua_instance(label=label)
    elif domain:
        restart_nua_instance(domain=domain)
    else:
        print("WIP: currently a label or domain must be provided.")


@app.command("backup")
def backup_cmd(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    all_apps: bool = option_all_apps,
    label: str = option_label,
    domain: str = option_domain,
):
    """Backup app instance(s) having a backup rules."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if all_apps:
        backup_all_apps()
    elif label or domain:
        backup_one_app(label=label, domain=domain)
    else:
        print("WIP: a label or domain must be provided or --all.")


@app.command("backup-restore")
def restore_last_backup_cmd(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
    label: str = option_label,
    domain: str = option_domain,
    list_flag: bool = option_list_backup,
    last_flag: bool = option_last_backup,
):
    """Restore backuped data for the app instance."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    if list_flag:
        return restore_list_backups(label=label, domain=domain)
    if label or domain:
        return restore_last_backup(label=label, domain=domain)
    print("WIP: currently a label or domain must be provided.")


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
