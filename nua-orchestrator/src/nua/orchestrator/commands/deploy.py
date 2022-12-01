"""Nua main scripts.

Rem: maybe need to refactor the "site" thing into a class and refactor a lot
"""
from nua.lib.tool.state import verbosity

from ..sites_deployment import SitesDeployment


def deploy_nua_sites(deploy_config: str) -> int:
    deployer = SitesDeployment()
    deployer.load_available_services()
    deployer.load_deploy_config(deploy_config)
    deployer.install_required_images()
    if verbosity(3):
        deployer.print_host_list()
    deployer.install_required_resources()
    deployer.configure_deployment_phase_1()
    deployer.deactivate_all_sites()
    deployer.configure_deployment_phase_2()
    deployer.start_sites()
    deployer.display_final()
