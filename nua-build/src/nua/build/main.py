"""Script to build a nua package

- information come from a mandatory local file: "nua-config" (.toml, .json, .yaml)
- origin may be a source tar.gz or a git repository or a docker image...
- build locally or wrap docker image

Note: **currently use "nua-build ..." for command line**.
See later if move this to "nua ...".
"""
from typing import Optional

import snoop
import typer
from cleez.colors import red

from nua.lib.panic import Abort
from nua.lib.tool.state import set_color, set_verbosity
from nua.agent.nua_config import NuaConfigError

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

    try:
        builder = get_builder(config_file)
    except NuaConfigError as e:
        print(red("Configuration error: " + e.args[0]))
        raise Abort(status=1) from e

    try:
        builder.run()
    except BuilderError as e:
        print(red("Build error: " + e.args[0]))
        raise Abort from e
