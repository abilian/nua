"""Script to build Nua own images."""
from typing import Optional

import typer
from nua.lib.tool.state import set_color, set_verbosity

from .. import __version__
from .nua_image_builder import NuaImageBuilder

app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        _version_string()
        raise typer.Exit(0)


option_force = typer.Option(
    False,
    "--force",
    "-f",
    help="Force build of images.",
)

option_download = typer.Option(
    False,
    "--download",
    "-d",
    help="Force download of Nua source code.",
)

option_all = typer.Option(
    True,
    "--all",
    "-a",
    help="Build all base images (Node.js, ...).",
)

option_version = typer.Option(
    None,
    "--version",
    "-V",
    help="Show package version and exit.",
    callback=version_callback,
    is_eager=True,
)

option_verbose = typer.Option(
    0, "--verbose", "-v", help="Show more information, until -vvv. ", count=True
)

option_color = typer.Option(True, "--color/--no-color", help="Colorize messages. ")


def _version_string():
    typer.echo(f"nua-self-build version: {__version__}")


# @app.callback(invoke_without_command=True)
@app.command()
def main(
    force: bool = option_force,
    download: bool = option_download,
    all: bool = option_all,
    verbose: int = option_verbose,
    colorize: bool = option_color,
    version: Optional[bool] = option_version,
):
    """Nua-self-build CLI inferface."""
    # Called as `nua-self-build`
    set_verbosity(verbose)
    set_color(colorize)

    image_builder = NuaImageBuilder()
    image_builder.build(force=force, download=download, all=all)
