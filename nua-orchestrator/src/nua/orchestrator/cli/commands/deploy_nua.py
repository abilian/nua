"""Nua deployment of Nua image itself.

WIP
"""
from nua.lib.console import print_magenta
from nua.lib.panic import abort
from nua.lib.tool.state import verbosity

from ...deploy_utils import load_install_image
from ...docker_utils import docker_service_start_if_needed
from ...search_cmd import search_nua


def deploy_nua(app_name: str) -> int:
    """Search, install and launch Nua image.

    (from local registry for now.)
    """
    # if app_name.endswith(".toml") and Path(app_name).is_file():
    #     return deploy_nua_sites(app_name)
    if verbosity(2):
        print_magenta(f"image: '{app_name}'")
    results = search_nua(app_name)
    if not results:
        abort(f"No image found for '{app_name}'.")

    # ensure docker is running
    docker_service_start_if_needed()

    # images are sorted by version, take the last one:
    image_id, image_nua_config = load_install_image(results[-1])
    deploy_image(image_id, image_nua_config)
    return 0


def deploy_image(image_id: str, image_nua_config: dict):
    # here will used core functions of the orchestrator
    # - see if image is already deployed
    # - see if image got specific deploy configuration
    # - build specifc config for nginx and others
    # - build docker run command
    # - finally execute docker command
    print("No implemented")
    pass
