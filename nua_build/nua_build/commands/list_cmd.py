"""List available images."""

import docker
import typer

from ..db import requests

app = typer.Typer()


def clean_list():
    """Clean list images known in Nua DB by comparing to images actually
    present in docker.

    Reason: it may append that docker images were deleted outside of Nua.
    """
    nuad_ids = requests.list_images_ids()
    client = docker.from_env()
    docker_ids = {img.id for img in client.images.list()}
    to_remove = [idx for idx in nuad_ids if idx not in docker_ids]
    if to_remove:
        requests.remove_ids(to_remove)


@app.command("list")
def list_cmd() -> None:
    """List local docker images of Nua packages."""
    clean_list()
    images_list = requests.list_images()
    images_list.append("")
    print("\n".join(images_list))
