"""API to access orchestrator commands."""
from pathlib import Path
from typing import Any

from nua.lib.tool.state import set_verbosity

from .app_deployment import AppDeployment
from .app_management import AppManagement
from .cli.commands.status import StatusCommand
from .config import config  # noqa: F401
from .db import store
from .db.store import list_all_settings
from .init import initialization
from .version import __version__  # noqa: F401


class API:
    """API to access orchestrator commands."""

    def __init__(self):
        initialization()
        set_verbosity(0)

    def call(self, method: str, **kwargs: Any) -> Any:
        return getattr(self, method)(**kwargs)

    def _status(self):
        """Send status information about local orchestrator installation."""
        status = StatusCommand()
        return status.as_dict()

    def status(self) -> dict[str, Any]:
        """Return status information as a dict."""
        status = StatusCommand()
        return status.as_dict()

    # wip ###################################################################

    def list(self):
        instances = store.list_instances_all()
        return [instance.to_dict() for instance in instances]

    def settings(self):
        return list_all_settings()

    def server_log(self):
        # FIXME: hardcoded for now (and not working because logfile not created)
        # with Path("/home/nua/log/nua_orchestrator.log").open() as f:
        with Path("/var/log/ubuntu-advantage.log").open() as f:
            return f.read()

    def backup(self):
        """Execute a one-time backup for all site instance having a backup
        declaration."""
        deployer = AppManagement()
        result = deployer.backup_apps()
        return result

    def deploy(self, deploy_config: dict) -> str:
        deployer = AppDeployment()
        deployer.local_services_inventory()
        # Not using the deployer method, need refactoring
        self._load_deploy_config(deployer, deploy_config)
        deployer.gather_requirements()
        deployer.configure_apps()
        deployer.deactivate_previous_apps()
        deployer.apply_nginx_configuration()
        deployer.start_apps()
        deployer.post_deployment()
        return "OK"

    def _load_deploy_config(self, deployer: AppDeployment, deploy_config: dict):
        deployer.loaded_config = deploy_config
        deployer.parse_deploy_apps()
        deployer.sort_apps_per_name_domain()

    def ping(self) -> str:
        return "pong"
