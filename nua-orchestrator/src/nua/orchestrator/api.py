"""API to access orchestrator commands."""
from pathlib import Path
from typing import Any

from nua.lib.tool.state import set_verbosity

from .app_deployment import AppDeployment
from .app_management import AppManagement
from .cli.commands.deploy_remove import deploy_merge_one_nua_app
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

    def status(self) -> dict[str, Any]:
        """Return status information about local orchestrator as a dict."""
        status = StatusCommand()
        return status.as_dict()

    def search(self, app_name: str) -> list[Path]:
        """Search Nua image from the registries.

        (local registry for now).

        Return:
            list of path of local Nua archives sorted by version.
        """
        return search_nua(app_name)

    def deploy_one(
        self,
        image: str,
        domain: str,
        label: str = "",
        **kwargs: Any,
    ) -> None:
        """Deploy one Nua applications."""
        deployment_conf = kwargs
        deployment_conf.update({"image": image, "domain": domain, "label": label})
        site_conf = {"site": [deployment_conf]}
        deploy_merge_one_nua_app(site_conf)

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
