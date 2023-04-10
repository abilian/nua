from operator import itemgetter
from pathlib import Path

from nua.orchestrator import __version__, config
from nua.orchestrator.app_deployment import AppDeployment
from nua.orchestrator.app_management import AppManagement
from nua.orchestrator.db import store
from nua.orchestrator.db.store import list_all_settings


class API:
    def call(self, method, **kwargs):
        return getattr(self, method)(**kwargs)

    def list(self):
        instances = store.list_instances_all()
        return [instance.to_dict() for instance in instances]

    def settings(self):
        return list_all_settings()

    def status(self):
        """Send some status information about local installation."""

        # fixme: go further on status details (sub servers...)
        def display_configured_registries():
            """Show configured registries."""
            registries = config.read("nua", "registry")
            print("Configured registries:")
            for reg in sorted(registries, key=itemgetter("priority")):
                msg = (
                    f'  priority: {reg["priority"]:>2}   '
                    f'format: {reg["format"]:<16}   '
                    f'url: {reg["url"]}'
                )
                print(msg)

        result = {}
        result["version"] = __version__
        result["registries"] = config.read("nua", "registry")
        return result

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
