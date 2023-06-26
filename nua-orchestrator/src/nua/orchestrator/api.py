"""API to access orchestrator commands."""
from pathlib import Path
from typing import Any

from nua.lib.tool.state import set_verbosity

from .cli.commands.deploy_remove import deploy_merge_one_nua_app_config
from .cli.commands.status import StatusCommand
from .db import store
from .db.store import list_all_settings
from .init import initialization
from .search_cmd import search_nua


class API:
    """API to access orchestrator commands."""

    def __init__(self):
        initialization()
        set_verbosity(-1)

    def call(self, method: str, **kwargs: Any) -> Any:
        return getattr(self, method)(**kwargs)

    @staticmethod
    def status() -> dict[str, Any]:
        """Return status information about local orchestrator as a dict."""
        status = StatusCommand()
        status.read()
        return status.as_dict()

    @staticmethod
    def search(app_name: str) -> list[Path]:
        """Search Nua image from the registries.

        (local registry for now).

        Return:
            list of path of local Nua archives sorted by version.
        """
        return search_nua(app_name)

    @staticmethod
    def deploy_one(
        image: str,
        domain: str,
        label: str = "",
        env: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Deploy one Nua applications."""
        app_config = kwargs
        app_config.update({"image": image, "domain": domain, "label": label})
        if env is not None:
            app_config["env"] = env
        deploy_merge_one_nua_app_config(app_config)

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

    # def backup(self):
    #     """Execute a one-time backup for all site instance having a backup
    #     declaration."""
    #     manager = AppManagement()
    #     result = manager.backup_apps()
    #     return result
