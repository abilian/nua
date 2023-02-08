import sys

import typer
from snoop import pp

from nua_cli.client import get_client
from nua_cli.common import get_current_app_id

app = typer.Typer()
client = get_client()


@app.command()
def show(app: str = typer.Option("", help="Id of the application.")):
    """Show application config."""
    result = client.call("list")

    app_id = app
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
