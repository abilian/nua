"""Restore previous successful deployed configuration.
"""
from nua.lib.tool.state import verbosity

from ..sites_deployment import SitesDeployment


def restore_nua_sites():
    deployer = SitesDeployment()
    deployer.local_services_inventory()
    deployer.restore_load_deploy_config()
    deployer.gather_requirements()
    deployer.restore_configure()
    deployer.restore_deactivate_previous_sites()
    deployer.apply_configuration()
    deployer.start_sites()
    deployer.post_deployment()
