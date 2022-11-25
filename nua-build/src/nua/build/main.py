"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nua-build ..." for command line**.
See later if move this to "nua ...".
"""
from typing import Optional

import typer
from nua.lib.rich_console import print_green
from nua.lib.tool.state import set_color, set_verbose

from . import __version__
from .commands.builder import Builder, build_nua_builder_if_needed

app = typer.Typer()

# app.registered_commands += build_cmd.app.registered_commands


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


argument_config = typer.Argument(
    None, metavar="config", help="Path to the package dir or 'nua-config.toml' file."
)

option_version = typer.Option(
    None,
    "--version",
    "-V",
    help="Show nua-build version and exit.",
    callback=version_callback,
    is_eager=True,
)

option_verbose = typer.Option(
    0, "--verbose", "-v", help="Show more informations, until -vvv. ", count=True
)

option_color = typer.Option(True, "--color/--no-color", help="Colorize messages. ")


def _version_string():
    typer.echo(f"nua-build version: {__version__}")


# def usage():
#     _version_string()
#     typer.echo(
#         "Usage: nua-build [OPTIONS] COMMAND [ARGS]...\n\n"
#         "Try 'nua-build --help' for help."
#     )
#     raise typer.Exit(0)


def initialization():
    pass


# @app.callback(invoke_without_command=True)
@app.command()
def main(
    # ctx: typer.Context,
    config_file: Optional[str] = argument_config,
    version: Optional[bool] = option_version,
    verbose: int = option_verbose,
    colorize: bool = option_color,
):
    """Nua-build CLI inferface."""
    set_verbose(verbose)
    set_color(colorize)
    initialization()
    build_nua_builder_if_needed()
    builder = Builder(config_file)
    print_green(f"*** Generation of the image for {builder.config.app_id} ***")
    builder.run()
