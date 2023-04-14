"""Nua main scripts."""
from nua.orchestrator.app_deployment import AppDeployment


def deploy_nua_apps(deploy_config: str):
    deployer = AppDeployment()
    deployer.local_services_inventory()
    deployer.load_deploy_config(deploy_config)
    deployer.gather_requirements()
    deployer.configure_apps()
    deployer.store_initial_deployment_state()
    deactivate_installed_apps()
    deployer.apply_nginx_configuration()
    deployer.start_apps()
    deployer.post_deployment()


def deactivate_installed_apps():
    uninstaller = AppDeployment()
    uninstaller.load_deployed_configuration()
    uninstaller.remove_all_deployed_nginx_configuration()
    uninstaller.stop_all_deployed_apps()
    uninstaller.remove_all_deployed_container_and_network()
    uninstaller.remove_all_deployed_managed_volumes()
    uninstaller.post_full_uninstall()
