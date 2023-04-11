"""Start/stop/restart some deployed app instance."""

from nua.orchestrator.app_deployment import AppDeployment


def start_nua_instance_domain(domain: str):
    """Start some deployed app instance.

    The instance is started (if it was already deployed).

    WIP: at the moment requires identification of the instance per domain name.
    """
    deployer = AppDeployment()
    starting_apps = deployer.instances_of_domain(domain)
    deployer.start_deployed_apps(domain, starting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployer.post_deployment()


def stop_nua_instance_domain(domain: str):
    """Stop some deployed app instance.

    The instance is stopped, but not uninstalled (volumes are kepts).

    WIP: at the moment requires identification of the instance per domain name.
    """
    deployer = AppDeployment()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.stop_deployed_apps(domain, stopping_apps)
    deployer.post_deployment()


def restart_nua_instance_domain(domain: str):
    """Restart some deployed app instance.

    WIP: at the moment requires identification of the instance per domain name.
    """
    deployer = AppDeployment()
    restarting_apps = deployer.instances_of_domain(domain)
    deployer.restart_deployed_apps(domain, restarting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployer.post_deployment()
