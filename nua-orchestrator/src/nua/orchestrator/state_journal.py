"""Class to to journalize state of the deployed apps."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from nua.lib.panic import Abort, important, info
from nua.lib.tool.state import verbosity

from .app_deployer import AppDeployer
from .app_instance import AppInstance
from .db.model.deployconfig import ACTIVE
from .db.store import (
    deploy_config_active,
    deploy_config_add_config,
    deploy_config_last_inactive,
    deploy_config_per_id,
    deploy_config_previous,
)
from .provider import Provider


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
        self.current: dict[str, Any] = {}

    def read_current_state(self) -> None:
        """Read the current deployed configuration from database."""
        self.current = deploy_config_active()
        if not self.current:
            # either
            # - first run or
            # - last deployment did crash with a PREVIOUS status somewhere
            # - or rare situation (active->inactive)
            self.current = deploy_config_previous()
        if not self.current:
            self.current = deploy_config_last_inactive()

    def read_previous_state(self) -> None:
        if not self.current:
            return
        self.current = deploy_config_per_id(self.current["previous"])

    def deployed_state(self) -> dict[str, Any]:
        """The last deployed state from the journal.

        Return a dict with:
            requested: dict of last site configuration request
            deployed: list of the configures Appinstance data
            state_id:  id of the DB record"""
        result = {"requested": {}, "apps": [], "state_id": -1}
        if self.current:
            result["requested"] = self.current["deployed"]["requested"]
            result["apps"] = self.current["deployed"]["apps"]
            result["state_id"] = self.current["id"]
        return result

    def store_deployed_state(self, deploy_config: dict[str, Any]) -> int:
        """Store in the Nua DB the deployed state.

        deploy_config = {"requested": requested, "apps": deepcopy(apps)}"""
        if self.current:
            previous_id = self.current["id"]
        else:
            previous_id = -1
        record = deploy_config_add_config(
            deploy_config,
            previous_id=previous_id,
            state=ACTIVE,
        )
        with verbosity(1):
            info(f"Store state number {record['id']}")
        self.current = record
        return record["id"]

    @staticmethod
    def _app_info(app: AppInstance, text: list[str]) -> None:
        text.append(f"    label: {app.label_id}")
        text.append(f"        app_id: {app.app_id}")
        text.append(f"        domain: {app.domain}")
        text.append(f"        nua_tag: {app.nua_tag}")
        text.append(f"        container_name: {app.container_name}")
        text.append(f"        container_id: {app.container_id_short}")

    @staticmethod
    def _provider_info(pro: Provider, text: list[str]) -> None:
        text.append(f"        provider name: {pro.provider_name}")
        text.append(f"            container_name: {pro.container_name}")
        text.append(f"            container_id: {pro.container_id_short}")

    def info(self) -> list[str]:
        text: list[str] = []
        if not self.current:
            return text
        doc = self.current
        text.append(f"State Id: {doc['id']}")
        text.append(f"Created : {doc['created']}")
        for app_data in doc["deployed"]["apps"]:
            app = AppInstance.from_dict(app_data)
            self._app_info(app, text)
            for provider in app.providers:
                self._provider_info(provider, text)
        return text


def info_last_deployments(number: int = 10) -> list[str]:
    text: list[str] = []
    state = StateJournal()
    state.read_current_state()
    while number > 0 and state.current:
        number -= 1
        text.extend(state.info())
        state.read_previous_state()
    return text
