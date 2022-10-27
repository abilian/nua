"""Nua main scripts.

Rem: maybe need to refactor the "site" thing into a class and refactor a lot
"""
from pprint import pformat

from ..sites_deployment import SitesDeployment
from ..state import verbosity


def deploy_nua_sites(deploy_config: str) -> int:
    deployer = SitesDeployment()
    deployer.load_available_services()
    deployer.load_deploy_config(deploy_config)
    deployer.install_required_images()
    if verbosity(3):
        print("'host_list':\n", pformat(deployer.host_list))
    deployer.deactivate_all_sites()
    deployer.configure_deployment()
    deployer.start_sites()
    deployer.display_final()
