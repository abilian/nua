"""Nua main scripts.

Rem: maybe need to refactor the "site" thing into a class and refactor a lot
"""
from nua.lib.tool.state import verbosity

from ..sites_deployment import SitesDeployment


def deploy_nua_sites(deploy_config: str) -> int:
    deployer = SitesDeployment()
    deployer.local_services_inventory()
    deployer.load_deploy_config(deploy_config)
    deployer.gather_requirements()
    deployer.configure()
    deployer.deactivate_previous_sites()
    deployer.apply_configuration()
    deployer.start_sites()
    deployer.display_final()
