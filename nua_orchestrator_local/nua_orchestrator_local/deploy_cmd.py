"""Nua main scripts.
"""
import sys
from pathlib import Path

import docker

from .archive_search import ArchiveSearch
from .docker_utils import display_one_docker_img, docker_service_start_if_needed
from .rich_console import print_green, print_magenta, print_red
from .search_cmd import parse_app_name, search_docker_tar_local


def deploy_nua(app_name: str) -> int:
    """Search, install and launch Nua image.

    (from local registry for now.)"""
    print_magenta(f"Deploy image '{app_name}'")
    app, tag = parse_app_name(app_name)
    results = search_docker_tar_local(app, tag)
    if not results:
        print_red(f"No image found for '{app_name}'.")
        sys.exit(1)
    # ensure docker is running
    docker_service_start_if_needed()
    # fixme: take higher version, not fist element:
    img_id, image_config = install_image(results[0])
    deploy_image(img_id, image_config)
    return 0


def install_image(image_path: str | Path) -> tuple:
    path = Path(image_path)
    # image is local, so we can mount it directly
    if not path.is_file():
        raise FileNotFoundError(path)
    arch_search = ArchiveSearch(path)
    image_config = arch_search.nua_config_dict()
    if not image_config:
        print_red(f"Error: image non compatible Nua: {path}.")
        raise ValueError("No Nua config found")
    metadata = image_config["metadata"]
    msg = "Installing: '{title}', ({id} {version})".format(**metadata)
    print_magenta(msg)
    client = docker.from_env()
    # images_before = {img.id for img in client.images.list()}
    with open(path, "rb") as input:  # noqa: S108
        loaded = client.images.load(input)
    if not loaded or len(loaded) > 1:
        print_red("Warning: loaded image result is strange:")
        print_red(f"{loaded=}")
    loaded_img = loaded[0]
    # images_after = {img.id for img in client.images.list()}
    # new = images_after - images_before
    print_green("Intalled image:")
    display_one_docker_img(loaded_img)
    return loaded_img.id, image_config


def deploy_image(img_id: str, image_config: dict):
    # here will used core functions of the orchestrator
    # - see if image is already deployed
    # - see if image got specific deploy configuration
    # - build specifc config for nginx and others
    # - build docker run command
    # - finally execute docker command
    pass
