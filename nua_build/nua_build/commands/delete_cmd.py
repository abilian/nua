"""Delete the docker build of an app."""
from contextlib import suppress
from typing import Optional

import docker
import typer

from ..db import requests
from .list_cmd import clean_list

app = typer.Typer()

argument_app_id = typer.Argument(
    None, metavar="app_id", help="Identifier of the app to suppress from docker builds."
)


@app.command("delete")
def load_nua_settings(app_id: Optional[str] = argument_app_id) -> None:
    """Delete the docker build of an app.

    (fixme: instances, versions...)
    """
    app_id = app_id.strip()
    if not app_id:
        return
    app_id = app_id.split(":")[0]
    id_list = requests.images_id_per_app_id(app_id)
    if not id_list and app_id.startswith("nua-"):
        # try by removing "nua-"
        app_id_short = app_id[4:]
        id_list = requests.images_id_per_app_id(app_id_short)
    if not id_list:
        print(f"No image found for '{app_id}'")
    client = docker.from_env()
    for idx in id_list:
        print(f"Removing docker image {idx}")
        with suppress(docker.errors.ImageNotFound):
            client.images.remove(image=idx, force=True, noprune=False)
        # see for docker.errors.APIError
    clean_list()
