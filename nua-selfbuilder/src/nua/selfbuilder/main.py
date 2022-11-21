"""Script to build Nua own images.
"""
from typing import Optional

import typer
from nua.lib.common.rich_console import print_green
from nua.lib.tool.state import set_verbose

from . import __version__
from .nua_image_builder import NUAImageBuilder

app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


argument_path = typer.Argument(
    ...,
    help="Work dir path.",
)


option_version = typer.Option(
    None,
    "--version",
    "-V",
    help="Show nua-selfbuilder version and exit.",
    callback=version_callback,
    is_eager=True,
)

option_verbose = typer.Option(
    0, "--verbose", "-v", help="Show more informations, until -vvv. ", count=True
)


def _version_string():
    typer.echo(f"nua-self-build version: {__version__}")


# @app.callback(invoke_without_command=True)
@app.command()
def main(
    version: Optional[bool] = option_version,
    verbose: int = option_verbose,
):
    """Nua-self-build CLI inferface."""
    set_verbose(verbose)
    image_builder = NUAImageBuilder(force=True)
    image_builder.run()
