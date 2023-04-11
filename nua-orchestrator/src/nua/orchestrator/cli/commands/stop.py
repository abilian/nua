"""Stop some deployed app instance."""

from nua.orchestrator.app_deployment import AppDeployment


def stop_nua_instance_domain(domain: str):
    """Stop some deployed app instance.

    The instance is stopped, but not uninstalled (volumes are kepts).

    WIP: at the moment requires identification of the instance per domain name.
    """
    deployer = AppDeployment()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.stop_apps(stopping_apps)
    deployer.post_deployment()
