"""Restore previous successful deployed configuration."""

from nua.orchestrator.sites_deployment import SitesDeployment


def restore_nua_sites_strict():
    """Restore to the most recent deployment configuration that did succed.

    - It will be the current one if the deployment did not fail.
    - Strict mode: try to reuse exactl same configuration, including internal ports
    numbers.
    """
    deployer = SitesDeployment()
    deployer.local_services_inventory()
    deployer.restore_previous_deploy_config_strict()
    deployer.gather_requirements()
    deployer.restore_configure()
    deployer.restore_deactivate_previous_sites()
    deployer.apply_configuration()
    deployer.start_sites()
    deployer.post_deployment()


def restore_nua_sites_replay():
    """Restore to the most recent deployment configuration that did succed.

    - It will be the current one if the deployment did not fail.
    - It is a simple 'replay' of the deployment request. So the internal used ports
    can be differents. It is the prefered option.
    """
    deployer = SitesDeployment()
    deployer.local_services_inventory()
    deployer.restore_previous_deploy_config_replay()
    deployer.gather_requirements()
    deployer.configure_sites()
    deployer.restore_deactivate_previous_sites()
    deployer.apply_configuration()
    deployer.start_sites()
    deployer.post_deployment()
