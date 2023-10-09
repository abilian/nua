"""Nua main scripts."""
from typing import Any

from nua.orchestrator.app_deployer import AppDeployer
from nua.orchestrator.state_journal import StateJournal, restore_if_fail


@restore_if_fail
def deploy_nua_apps(deploy_config: str, state_journal: StateJournal):
    deployer = AppDeployer()
    deployer.local_services_inventory()
    deployer.load_deploy_config(deploy_config)
    deployer.gather_requirements()
    deployer.configure_apps()
    _deactivate_installed_apps(state_journal)
    deployer.apply_nginx_configuration()
    deployer.start_apps()
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


def _deactivate_installed_apps(state_journal: StateJournal):
    uninstaller = AppDeployer()
    uninstaller.load_deployed_state(state_journal.deployed_state())
    uninstaller.remove_all_deployed_nginx_configuration()
    uninstaller.stop_all_deployed_apps()
    uninstaller.remove_all_deployed_container_and_network()
    uninstaller.remove_all_deployed_managed_volumes()
    uninstaller.post_full_uninstall()


@restore_if_fail
def remove_nua_domain(domain: str, state_journal: StateJournal):
    """Remove some deployed app instance, erasing its data and container.

    Deprecated: requires identification of the instance per domain name.
    """
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    stopping_apps = deployer.instances_of_domain(domain)
    deployer.remove_nginx_configuration(domain)
    deployer.remove_app_list(stopping_apps)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def remove_nua_label(label: str, state_journal: StateJournal):
    """Remove some deployed app instance, erasing its data and container."""
    deployer = AppDeployer()
    deployer.load_deployed_state(state_journal.deployed_state())
    removed_app = deployer.instance_of_label(label)
    deployer.remove_nginx_configuration(removed_app.domain)
    deployer.remove_app_list([removed_app])
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def deploy_merge_nua_app(merge_config: str, state_journal: StateJournal):
    """Add somme app config to the deployed list."""
    deployer = AppDeployer()
    deployer.local_services_inventory()
    deployer.load_deployed_state(state_journal.deployed_state())
    additional = AppDeployer()
    additional.local_services_inventory()
    additional.load_deploy_config(merge_config)
    additional.gather_requirements()
    deployer.merge_sequential(additional)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()


@restore_if_fail
def deploy_merge_one_nua_app_config(
    app_config: dict[str, Any], state_journal: StateJournal
) -> None:
    """Add somme app config to the deployed list."""
    deployer = AppDeployer()
    deployer.local_services_inventory()
    deployer.load_deployed_state(state_journal.deployed_state())
    additional = AppDeployer()
    additional.local_services_inventory()
    additional.load_one_app_config(app_config)
    additional.gather_requirements()
    deployer.merge_sequential(additional)
    deployed = deployer.deployed_configuration()
    state_journal.store_deployed_state(deployed)
    deployer.display_deployment_status()
