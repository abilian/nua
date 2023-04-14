"""Nua main scripts."""
from nua.orchestrator.app_deployment import AppDeployment


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


def deploy_merge_nua_app(merge_config: str):
    """Add somme app config to the deplyed list."""
    deployer = AppDeployment()
    deployer.local_services_inventory()
    deployer.load_deployed_configuration()
    additional = AppDeployment()
    additional.local_services_inventory()
    additional.load_deploy_config(merge_config)
    additional.gather_requirements()
    deployer.merge(additional)
    deployer.post_deployment()
