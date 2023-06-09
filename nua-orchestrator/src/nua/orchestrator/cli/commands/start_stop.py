"""Start/stop/restart some deployed app instance."""

from nua.orchestrator.app_deployment import AppDeployment


def stop_nua_instance(*, label: str = "", domain: str = ""):
    """Stop some deployed app instance per label or per domain."""
    if label:
        stop_nua_instance_label(label)
    else:
        stop_nua_instance_domain(domain)


def start_nua_instance(*, label: str = "", domain: str = ""):
    """Start some deployed app instance per label or per domain."""
    if label:
        start_nua_instance_label(label)
    else:
        start_nua_instance_domain(domain)


def restart_nua_instance(*, label: str = "", domain: str = ""):
    """Restart some deployed app instance per label or per domain."""
    if label:
        restart_nua_instance_label(label)
    else:
        restart_nua_instance_domain(domain)


def start_nua_instance_domain(domain: str):
    """Start some deployed app instance (per domain).

    The instance is started (if it was already deployed).
    """
    deployer = AppDeployment()
    starting_apps = deployer.instances_of_domain(domain)
    deployer.start_deployed_apps(starting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployer.post_deployment()


def start_nua_instance_label(label: str):
    """Start some deployed app instance (per label).

    The instance is started (if it was already deployed).
    """
    deployer = AppDeployment()
    starting_app = deployer.instance_of_label(label)
    deployer.start_deployed_apps([starting_app])
    deployer.reconfigure_nginx_domain(starting_app.domain)
    deployer.post_deployment()


def stop_nua_instance_domain(domain: str):
    """Stop some deployed app instance (per domain).

    The instance is stopped, but not uninstalled (volumes are kept).
    """
    deployer = AppDeployment()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.stop_deployed_apps(stopping_apps)
    deployer.post_deployment()


def stop_nua_instance_label(label: str):
    """Stop some deployed app instance (per label).

    The instance is stopped, but not uninstalled (volumes are kept).
    """
    deployer = AppDeployment()
    stopping_app = deployer.instance_of_label(label)
    deployer.remove_nginx_configuration(stopping_app.domain)
    deployer.stop_deployed_apps([stopping_app])
    deployer.post_deployment()


def restart_nua_instance_domain(domain: str):
    """Restart some deployed app instance  (per domain)."""
    deployer = AppDeployment()
    restarting_apps = deployer.instances_of_domain(domain)
    deployer.restart_deployed_apps(restarting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployer.post_deployment()


def restart_nua_instance_label(label: str):
    """Restart some deployed app instance (per label)."""
    deployer = AppDeployment()
    restarting_app = deployer.instance_of_label(label)
    deployer.restart_deployed_apps([restarting_app])
    deployer.reconfigure_nginx_domain(restarting_app.domain)
    deployer.post_deployment()


def pause_nua_instance(*, label: str = "", domain: str = ""):
    """Stop some deployed app instance per label or per domain."""
    if label:
        pause_nua_instance_label(label)
    else:
        pause_nua_instance_domain(domain)


def unpause_nua_instance(*, label: str = "", domain: str = ""):
    """Start some deployed app instance per label or per domain."""
    if label:
        unpause_nua_instance_label(label)
    else:
        unpause_nua_instance_domain(domain)


def pause_nua_instance_domain(domain: str):
    """Pause some deployed app instance (per domain)."""
    deployer = AppDeployment()
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.pause_deployed_apps(stopping_apps)
    deployer.post_deployment()


def pause_nua_instance_label(label: str):
    """Pause some deployed app instance (per label)."""
    deployer = AppDeployment()
    stopping_app = deployer.instance_of_label(label)
    deployer.remove_nginx_configuration(stopping_app.domain)
    deployer.pause_deployed_apps([stopping_app])
    deployer.post_deployment()


def unpause_nua_instance_domain(domain: str):
    """Unpause some deployed app instance (per domain)."""
    deployer = AppDeployment()
    starting_apps = deployer.instances_of_domain(domain)
    deployer.unpause_deployed_apps(starting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployer.post_deployment()


def unpause_nua_instance_label(label: str):
    """Unpause some deployed app instance (per label)."""
    deployer = AppDeployment()
    starting_app = deployer.instance_of_label(label)
    deployer.unpause_deployed_apps([starting_app])
    deployer.reconfigure_nginx_domain(starting_app.domain)
    deployer.post_deployment()
