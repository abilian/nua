"""Start/stop/restart some deployed app instance."""
from nua.orchestrator.app_deployer import AppDeployer
from nua.orchestrator.state_journal import StateJournal, restore_if_fail


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


@restore_if_fail
def start_nua_instance_domain(domain: str, state_journal: StateJournal):
    """Start some deployed app instance (per domain).

    The instance is started (if it was already deployed).
    """
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    starting_apps = deployer.instances_of_domain(domain)
    deployer.start_deployed_apps(starting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def start_nua_instance_label(label: str, state_journal: StateJournal):
    """Start some deployed app instance (per label).

    The instance is started (if it was already deployed).
    """
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    starting_app = deployer.instance_of_label(label)
    deployer.start_deployed_apps([starting_app])
    deployer.reconfigure_nginx_domain(starting_app.domain)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def stop_nua_instance_domain(domain: str, state_journal: StateJournal):
    """Stop some deployed app instance (per domain).

    The instance is stopped, but not uninstalled (volumes are kept).
    """
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.stop_deployed_apps(stopping_apps)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def stop_nua_instance_label(label: str, state_journal: StateJournal):
    """Stop some deployed app instance (per label).

    The instance is stopped, but not uninstalled (volumes are kept).
    """
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    stopping_app = deployer.instance_of_label(label)
    deployer.remove_nginx_configuration(stopping_app.domain)
    deployer.stop_deployed_apps([stopping_app])
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def restart_nua_instance_domain(domain: str, state_journal: StateJournal):
    """Restart some deployed app instance  (per domain)."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    restarting_apps = deployer.instances_of_domain(domain)
    deployer.restart_deployed_apps(restarting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def restart_nua_instance_label(label: str, state_journal: StateJournal):
    """Restart some deployed app instance (per label)."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    restarting_app = deployer.instance_of_label(label)
    deployer.restart_deployed_apps([restarting_app])
    deployer.reconfigure_nginx_domain(restarting_app.domain)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


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


@restore_if_fail
def pause_nua_instance_domain(domain: str, state_journal: StateJournal):
    """Pause some deployed app instance (per domain)."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.pause_deployed_apps(stopping_apps)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def pause_nua_instance_label(label: str, state_journal: StateJournal):
    """Pause some deployed app instance (per label)."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    stopping_app = deployer.instance_of_label(label)
    deployer.remove_nginx_configuration(stopping_app.domain)
    deployer.pause_deployed_apps([stopping_app])
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def unpause_nua_instance_domain(domain: str, state_journal: StateJournal):
    """Unpause some deployed app instance (per domain)."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    starting_apps = deployer.instances_of_domain(domain)
    deployer.unpause_deployed_apps(starting_apps)
    deployer.reconfigure_nginx_domain(domain)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def unpause_nua_instance_label(label: str, state_journal: StateJournal):
    """Unpause some deployed app instance (per label)."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    starting_app = deployer.instance_of_label(label)
    deployer.unpause_deployed_apps([starting_app])
    deployer.reconfigure_nginx_domain(starting_app.domain)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()
