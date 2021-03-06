"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nua-build ..." for command line**.
See later if move this to "nua ...".
"""
from typing import Optional

import typer

from . import __version__
from .commands.build_cmd import Builder, build_nua_builder_if_needed
from .rich_console import print_green

state = {"verbose": False}

app = typer.Typer()

# app.registered_commands += build_cmd.app.registered_commands


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


argument_config = typer.Argument(
    None, metavar="config", help="Path to the package dir or 'nua-config.toml' file."
)
# option_verbose = typer.Option(False, help="Print build log.")


option_version = typer.Option(
    None,
    "--version",
    "-V",
    help="Show nua-build version and exit.",
    callback=version_callback,
    is_eager=True,
)

option_verbose = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Write verbose output.",
)


def _version_string():
    typer.echo(f"nua-build version: {__version__}")


# def usage():
#     _version_string()
#     typer.echo(
#         "Usage: nua-build [OPTIONS] COMMAND [ARGS]...\n\nTry 'nua-build --help' for help."
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
    verbose: bool = option_verbose,
):
    """Nua-build CLI inferface."""
    initialization()
    if verbose:
        typer.echo("(Will write verbose output)")
        state["verbose"] = True
    # if ctx.invoked_subcommand is None:
    #     usage()
    build_nua_builder_if_needed(verbose)
    builder = Builder(config_file, verbose)
    print_green(f"*** Generation of the docker image for {builder.config.app_id} ***")
    builder.setup_build_directory()
    builder.build_with_docker()
