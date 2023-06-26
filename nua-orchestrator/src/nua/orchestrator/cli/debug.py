"""Script main entry point for Nua local."""
from pprint import pformat

import typer
from nua.lib.tool.state import set_color, set_verbosity

from ..app_manager import AppManager
from ..db.store import installed_nua_settings, list_all_settings
from ..init import initialization

ALLOW_SUFFIX = {".json", ".toml", ".yaml", ".yml"}

app = typer.Typer()
is_initialized = False

opt_verbose = typer.Option(
    0, "--verbose", "-v", help="Show more informations, until -vvv.", count=True
)
option_color = typer.Option(True, "--color/--no-color", help="Colorize messages.")


@app.command("deployed-config")
def deployed_config(
    verbose: int = opt_verbose,
    colorize: bool = option_color,
):
    """Debug: show current active configuration."""
    set_verbosity(verbose)
    set_color(colorize)
    initialization()
    deployer = AppManager()
    deployer.load_active_config()
    print(pformat(deployer.active_config))


@app.command("db-settings")
def db_settings():
    """Debug: show settings in db."""
    initialization()
    print(pformat(list_all_settings()))


@app.command("nua-settings")
def nua_settings():
    """Debug: show Nua orchestrator settings in db."""
    initialization()
    print(pformat(installed_nua_settings()))


@app.callback()
def main():
    """Debug commands."""
