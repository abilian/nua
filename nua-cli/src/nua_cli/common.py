from __future__ import annotations

from pathlib import Path

import tomli

# from .version import get_version


# def _version_callback(value: bool) -> None:
#     if value:
#         print_version()
#         raise typer.Exit(0)
#
#
# OPTS = {
#     "version": typer.Option(
#         None,
#         "--version",
#         "-V",
#         help="Show Nua version and exit.",
#         callback=_version_callback,
#         is_eager=True,
#     ),
#     "verbose": typer.Option(
#         0, "--verbose", "-v", help="Show more informations, until -vvv.", count=True
#     ),
#     "color": typer.Option(True, "--color/--no-color", help="Colorize messages."),
# }
#
#
# def print_version() -> None:
#     typer.echo(f"Nua CLI version: {get_version()}")


def get_current_app_id() -> str:
    """Get the current app id (if possible)."""
    try:
        config = get_current_app_config()
        return config["metadata"]["id"]
    except ValueError:
        return ""


def get_current_app_config() -> dict:
    config_file = Path("nua-config.toml")
    if not config_file.exists():
        config_file = Path("nua/nua-config.toml")
    if not config_file.exists():
        raise ValueError("No nua-config.toml found.")

    config_file = Path("nua/nua-config.toml")
    config_data = config_file.read_text()
    return tomli.loads(config_data)
