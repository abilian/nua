"""Nua main scripts."""
from nua.orchestrator.app_deployment import AppDeployment


def remove_nua_domain(domain: str):
    """Remove some deployed app instance, erasing its data and container.

    WIP: at the moment requires identification of the instance per domain name.
    """
    deployer = AppDeployment()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.stop_deployed_apps(domain, stopping_apps)
    deployer.remove_data(domain, stopping_apps)
    deployer.post_deployment()
    print("not implemented")
