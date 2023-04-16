"""Script to build a nua package (experimental)

- information come from a mandatory local file: "nua-config" (.toml, .json, .yaml)
- origin may be a source tar.gz or a git repository or a docker image...
- build locally or wrap docker image

Note: **currently use "nua-build ..." for command line**.
See later if move this to "nua ...".
"""
from typing import Optional

import snoop
import typer
from nua.lib.panic import Abort
from nua.lib.tool.state import set_color, set_verbosity

from . import __version__
from .builders import BuilderError, get_builder

snoop.install()

app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


argument_config = typer.Argument(
    None, metavar="config", help="Path to the package dir or 'nua-config' file."
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


def _version_string() -> None:
    typer.echo(f"nua-build version: {__version__}")


# def usage():
#     _version_string()
#     typer.echo(
#         "Usage: nua-build [OPTIONS] COMMAND [ARGS]...\n\n"
#         "Try 'nua-build --help' for help."
#     )
#     raise typer.Exit(0)


# @app.callback(invoke_without_command=True)
@app.command()
def main(
    # ctx: typer.Context,
    config_file: Optional[str] = argument_config,
    version: Optional[bool] = option_version,
    verbose: int = option_verbose,
    colorize: bool = option_color,
) -> None:
    """Nua-build CLI inferface."""
    set_verbosity(verbose)
    set_color(colorize)

    builder = get_builder(config_file)
    try:
        builder.run()
    except BuilderError as e:
        raise Abort from e
