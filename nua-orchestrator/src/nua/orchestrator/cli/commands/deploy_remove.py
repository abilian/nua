"""Nua main scripts."""
from nua.lib.panic import Abort, vprint_magenta
from nua.lib.tool.state import verbosity

from nua.orchestrator.app_deployment import AppDeployment

from ...deploy_utils import load_install_image
from ...docker_utils import docker_service_start_if_needed
from ...search_cmd import search_nua


def deploy_nua_apps(deploy_config: str):
    deployer = AppDeployment()
    deployer.local_services_inventory()
    deployer.load_deploy_config(deploy_config)
    deployer.gather_requirements()
    deployer.configure_apps()
    deployer.store_initial_deployment_state()
    _deactivate_installed_apps()
    deployer.apply_nginx_configuration()
    deployer.start_apps()
    deployer.post_deployment()


def _deactivate_installed_apps():
    uninstaller = AppDeployment()
    uninstaller.load_deployed_configuration()
    uninstaller.remove_all_deployed_nginx_configuration()
    uninstaller.stop_all_deployed_apps()
    uninstaller.remove_all_deployed_container_and_network()
    uninstaller.remove_all_deployed_managed_volumes()
    uninstaller.post_full_uninstall()


def remove_nua_domain(domain: str):
    """Remove some deployed app instance, erasing its data and container.

    WIP: at the moment requires identification of the instance per domain name.
    """
    deployer = AppDeployment()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.stop_deployed_apps(domain, stopping_apps)
    deployer.remove_container_and_network(domain, stopping_apps)
    deployer.remove_managed_volumes(stopping_apps)
    deployer.remove_deployed_instance(domain, stopping_apps)
    deployer.post_deployment()


def deploy_nua(app_name: str) -> int:
    """Search, install and launch Nua image.

    (from local registry for now.)
    """
    # if app_name.endswith(".toml") and Path(app_name).is_file():
    #     return deploy_nua_apps(app_name)
    with verbosity(2):
        vprint_magenta(f"image: '{app_name}'")
    results = search_nua(app_name)
    if not results:
        raise Abort(f"No image found for the app id '{app_name}'.")

    # ensure docker is running
    docker_service_start_if_needed()

    # images are sorted by version, take the last one:
    image_id, image_nua_config = load_install_image(results[-1])
    deploy_image(image_id, image_nua_config)
    return 0


def deploy_image(image_id: str, image_nua_config: dict):
    # here we will use core functions of the orchestrator
    # - see if image is already deployed
    # - see if image got specific deploy configuration
    # - build specifc config for nginx and others
    # - build docker run command
    # - finally execute docker command
    print("No implemented")
    pass
