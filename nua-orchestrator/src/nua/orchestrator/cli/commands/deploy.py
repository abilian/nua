"""Nua main scripts."""
from nua.orchestrator.sites_deployment import SitesDeployment


def deploy_nua_sites(deploy_config: str):
    deployer = SitesDeployment()
    deployer.local_services_inventory()
    deployer.load_deploy_config(deploy_config)
    deployer.gather_requirements()
    deployer.configure_sites()
    deployer.deactivate_previous_sites()
    deployer.apply_configuration()
    deployer.start_sites()
    deployer.post_deployment()
