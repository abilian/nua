"""Nua main scripts."""
from pprint import pformat

from nua.orchestrator.app_deployment import AppDeployment


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
