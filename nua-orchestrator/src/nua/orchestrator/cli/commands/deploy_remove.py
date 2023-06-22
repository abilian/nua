"""Nua main scripts."""
from collections.abc import Callable
from functools import wraps
from typing import Any

from nua.lib.panic import Abort

from nua.orchestrator.app_deployer import AppDeployer

from .restore_deployed import restore_nua_apps_strict


def restore_if_fail(func: Callable):
    """Restore last known stable state if installation failed."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except (OSError, RuntimeError, Abort):
            print("Try to restore last stable state.")
            restore_nua_apps_strict()

    return wrapper


@restore_if_fail
def deploy_nua_apps(deploy_config: str):
    deployer = AppDeployer()
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
    uninstaller = AppDeployer()
    uninstaller.load_deployed_configuration()
    uninstaller.remove_all_deployed_nginx_configuration()
    uninstaller.stop_all_deployed_apps()
    uninstaller.remove_all_deployed_container_and_network()
    uninstaller.remove_all_deployed_managed_volumes()
    uninstaller.post_full_uninstall()


@restore_if_fail
def remove_nua_domain(domain: str):
    """Remove some deployed app instance, erasing its data and container.

    Deprecated: requires identification of the instance per domain name.
    """
    deployer = AppDeployer()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.remove_app_list(stopping_apps)
    deployer.post_deployment()


@restore_if_fail
def remove_nua_label(label: str):
    """Remove some deployed app instance, erasing its data and container."""
    deployer = AppDeployer()
    removed_app = deployer.instance_of_label(label)
    deployer.remove_nginx_configuration(removed_app.domain)
    deployer.remove_app_list([removed_app])
    deployer.post_deployment()


@restore_if_fail
def deploy_merge_nua_app(merge_config: str):
    """Add somme app config to the deplyed list."""
    deployer = AppDeployer()
    deployer.local_services_inventory()
    deployer.load_deployed_configuration()
    additional = AppDeployer()
    additional.local_services_inventory()
    additional.load_deploy_config(merge_config)
    additional.gather_requirements()
    deployer.merge_sequential(additional)
    deployer.post_deployment()


@restore_if_fail
def deploy_merge_one_nua_app_config(app_config: dict[str, Any]) -> None:
    """Add somme app config to the deplyed list."""
    deployer = AppDeployer()
    deployer.local_services_inventory()
    deployer.load_deployed_configuration()
    additional = AppDeployer()
    additional.local_services_inventory()
    additional.load_one_app_config(app_config)
    additional.gather_requirements()
    deployer.merge_sequential(additional)
    deployer.post_deployment()
