"""Class to to journalize state of the deployed apps."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from nua.lib.panic import Abort

from .app_deployer import AppDeployer
from .db.model.deployconfig import ACTIVE
from .db.store import (
    deploy_config_active,
    deploy_config_add_config,
    deploy_config_last_inactive,
    deploy_config_previous,
)


def restore_if_fail(func: Callable):
    """Restore last known stable state if installation failed."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = StateJournal()
        state.fetch_current()
        try:
            return func(*args, state_journal=state, **kwargs)
        except (OSError, RuntimeError, Abort):
            print("Try to restore last stable state.")
            restore_from_state_journal(state)

    return wrapper


def restore_from_state_journal(state: StateJournal):
    """Restore to the most recent deployment configuration that did succeed."""
    deployer = AppDeployer()
    deployer.local_services_inventory()
    requested_config, apps = state.deployed_configuration()
    deployer.load_from_deployed_config(requested_config, apps)
    deployer.gather_requirements(parse_providers=False)
    deployer.restore_configure()
    deployer.restore_deactivate_previous_apps()
    deployer.apply_nginx_configuration()
    deployer.start_apps()
    deployer.display_deployment_status()


class StateJournal:
    def __init__(self):
        self.previous: dict[str, Any] = {}

    def fetch_current(self):
        self.previous = deploy_config_active()
        if not self.previous:
            # either
            # - first run or
            # - last deployment did crash with a PREVIOUS status somewhere
            # - or rare situation (active->inactive)
            self.previous = deploy_config_previous()
        if not self.previous:
            self.previous = deploy_config_last_inactive()

    def deployed_configuration(self) -> tuple[Any, Any]:
        if not self.previous:
            return ({}, [])
        deployed = self.previous["deployed"]
        return (deployed["requested"], deployed["apps"])

    def store_apps_configuration(self, deploy_config: dict[str, Any]):
        """deploy_config = {"requested": requested, "apps": deepcopy(apps)}"""
        if self.previous:
            previous_id = self.previous["id"]
        else:
            previous_id = -1
        record = deploy_config_add_config(
            deploy_config,
            previous_id=previous_id,
            state=ACTIVE,
        )
        print("state:", record["id"])
        self.previous = record
