from operator import itemgetter
from pprint import pp

import typer

from nua_cli.client import get_client

app = typer.Typer(name="server")
client = get_client()


@app.command()
def logs(service: str = typer.Argument("", help="Service to show logs for")):
    """Show server logs."""
    if not service:
        print("Service must be one of: nua, letsencrypt, nginx")

    match service:
        case "nua":
            print("Showing Nua logs [TODO]")
        case "letsencrypt":
            result = client.ssh("cat log/letsencrypt/letsencrypt.log")
            print(result.stdout)
        case "nginx":
            print("Showing Nginx logs [TODO]")
        case _:
            raise typer.BadParameter("Service must be one of: nua, letsencrypt, nginx")


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


@app.callback()
def main():
    """Manage the Nua server."""
