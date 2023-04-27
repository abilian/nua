"""Local docker registry.

WIP:
- at the moment, only use local docker configuratin of the host
- next step: configure a local registry, still using the 'registry' image,
  but behind a nginx server with authentication and a managed directory
  for storage.
"""

import sys
from pathlib import Path

import docker
from nua.lib.docker import image_created_as_iso

from . import config
from .db import store

# need something like: fuser -k 5001/tcp


def start_registry_container():
    fetch_registry_if_needed()
    run_regitry_container()


def run_regitry_container():
    client = docker.from_env()
    # maybe already running:
    conf = config.read("nua", "registry", "local")
    registry_tag = conf["container"]["tag"]
    registry_name = conf["container"]["name"]
    running = client.containers.list(filters={"name": registry_name})
    if running:
        return running[0]
    volume_env = conf["volume"]["env"]
    volume_path = Path(conf["volume"]["path"])
    volume_path.mkdir(mode=0o755, parents=True, exist_ok=True)
    container = client.containers.run(
        registry_tag,
        detach=True,
        ports={
            f"{conf.get('cont_port')}/tcp": (
                conf.get("address"),
                f"{conf.get('host_use')}",
            )
        },
        environment={volume_env: str(volume_path)},
        name=registry_name,
    )
    return container


def fetch_registry_if_needed():
    registry_tag = config.read("nua", "registry", "local", "container", "tag")
    locally_found = chech_image_in_local_registry(registry_tag)
    if not locally_found:
        image = pull_remote_image(registry_tag)
        store.store_image(
            id_sha=image.id,
            app_id="orig-registry",
            nua_tag=registry_tag,  # so: not a nua tag starting by "nua-"
            created=image_created_as_iso(image),
            size=image.attrs["Size"],
            data={},
        )


def pull_remote_image(tag: str):
    """Pull image from Docker hub.

    Return: docker.Image()
    """
    client = docker.from_env()
    image = client.images.pull(tag)
    return image


# SF: I don't understand the name of this function
def chech_image_in_local_registry(tag: str) -> bool:
    found = False
    message = None
    # here, the nua tag is the origian tag. Could be ok for common use images
    # like ubuntu, registry ...
    db_result = store.get_image_by_nua_tag(tag)
    if db_result:
        client = docker.from_env()
        result = client.images.list(filters={"reference": tag})
        if result:
            found = True
        else:
            message = f"Image '{tag}' not found in docker local db: " "pull required."
    else:
        message = f"Image '{tag}' not found locally: pull required."
    if message:
        print(message, file=sys.stderr)
    return found
