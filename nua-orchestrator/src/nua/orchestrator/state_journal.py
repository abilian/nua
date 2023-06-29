"""Class to to journalize state of the deployed apps."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from nua.lib.panic import Abort, info, important
from nua.lib.tool.state import verbosity

from .app_deployer import AppDeployer
from .db.model.deployconfig import ACTIVE
from .db.store import (
    deploy_config_active,
    deploy_config_add_config,
    deploy_config_last_inactive,
    deploy_config_previous,
)


def restore_if_fail(func: Callable):
    """Decorator: restore last known stable state if installation failed."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = StateJournal()
        state.read_current_state()
        kwargs["state_journal"] = state
        try:
            return func(*args, **kwargs)
        except (OSError, RuntimeError, Abort):
            important("Restore last stable state.")
            restore_from_state_journal(state)

    return wrapper


def restore_from_state_journal(state: StateJournal):
    """Restore to the most recent deployment configuration that did succeed."""
    deployer = AppDeployer()
    deployer.local_services_inventory()
    deployer.load_deployed_state(state.deployed_state())
    deployer.gather_requirements(parse_providers=False)
    deployer.restore_configure()
    deployer.restore_deactivate_previous_apps()
    deployer.apply_nginx_configuration()
    deployer.start_apps()
    deployed = deployer.deployed_configuration()
    state.store_deployed_state(deployed)
    deployer.display_deployment_status()


class StateJournal:
    """
    Thin wrapper class to access the DeployConfig table of the Nua config database.

    Use to store or retreive the active deployed configuration.

    DeployConfig fields are:
        id = Column(Integer, primary_key=True, autoincrement=True)
        previous = Column(Integer)
        state = Column(String(16), default=INACTIVE)
        created = Column(String(40))
        modified = Column(String(40))
        deployed = Column(JSON)
    """

    def __init__(self):
        self.previous: dict[str, Any] = {}

    def read_current_state(self) -> None:
        """Read the current deployed configuration from database."""
        self.previous = deploy_config_active()
        if not self.previous:
            # either
            # - first run or
            # - last deployment did crash with a PREVIOUS status somewhere
            # - or rare situation (active->inactive)
            self.previous = deploy_config_previous()
        if not self.previous:
            self.previous = deploy_config_last_inactive()

    def deployed_state(self) -> dict[str, Any]:
        """The last deployed state from the journal.

        Return a dict with:
            requested: dict of last site configuration request
            deployed: list of the configures Appinstance data
            state_id:  id of the DB record"""
        result = {"requested": {}, "apps": [], "state_id": -1}
        if self.previous:
            result["requested"] = self.previous["deployed"]["requested"]
            result["apps"] = self.previous["deployed"]["apps"]
            result["state_id"] = self.previous["id"]
        return result

    def store_deployed_state(self, deploy_config: dict[str, Any]) -> int:
        """Store in the Nua DB the deployed state.

        deploy_config = {"requested": requested, "apps": deepcopy(apps)}"""
        if self.previous:
            previous_id = self.previous["id"]
        else:
            previous_id = -1
        record = deploy_config_add_config(
            deploy_config,
            previous_id=previous_id,
            state=ACTIVE,
        )
        with verbosity(1):
            info(f"Store state number {record['id']}")
        self.previous = record
        return record["id"]
