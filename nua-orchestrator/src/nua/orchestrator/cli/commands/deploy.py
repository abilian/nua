"""Nua main scripts."""
from nua.orchestrator.app_deployment import AppDeployment


def deploy_nua_apps(deploy_config: str):
    deployer = AppDeployment()
    deployer.local_services_inventory()
    deployer.load_deploy_config(deploy_config)
    deployer.gather_requirements()
    deployer.configure_apps()
    deployer.deactivate_previous_apps()
    deployer.apply_nginx_configuration()
    deployer.start_apps()
    deployer.post_deployment()
