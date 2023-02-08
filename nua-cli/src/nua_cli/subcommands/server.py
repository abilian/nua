from operator import itemgetter

import typer
from snoop import pp

from nua_cli.client import get_client

app = typer.Typer()
client = get_client()


@app.command()
def logs():
    print("Showing logs [TODO]")


@app.command()
def status():
    """Show Nua status."""
    result = client.call("status")

    print(f"Nua version: {result['version']}")

    registries = result["registries"]
    print("Configured registries:")
    for reg in sorted(registries, key=itemgetter("priority")):
        msg = (
            f'  priority: {reg["priority"]:>2}   '
            f'format: {reg["format"]:<16}   '
            f'url: {reg["url"]}'
        )
        print(msg)


@app.command()
def settings():
    """Show server settings."""
    result = client.call("settings")
    pp(result)
