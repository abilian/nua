import sys
from pprint import pp

import typer

from nua_cli.client import get_client
from nua_cli.common import get_current_app_id

cli = typer.Typer(name="config")
client = get_client()


@cli.command()
def show(app_id: str = typer.Argument("", help="Id of the application.")):
    """Show application config."""
    result = client.call("list")

    if not app_id:
        app_id = get_current_app_id()
    if not app_id:
        typer.secho("No app_id specified", fg=typer.colors.RED)
        sys.exit(1)

    for instance in result:
        if instance["app_id"] == app_id:
            pp(instance)
            break
    else:
        typer.secho(f"App {app_id} not found", fg=typer.colors.RED)
        sys.exit(1)


@cli.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show/edit application config."""
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
