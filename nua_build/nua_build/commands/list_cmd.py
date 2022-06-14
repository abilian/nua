"""List available images."""

import typer

from ..db import requests

app = typer.Typer()


@app.command("list")
def build_cmd() -> None:
    """List local docker images of Nua packages."""
    requests.print_images()
