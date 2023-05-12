"""class to manage the currently active apps.

General use:
    - load active configuration
    - loop over apps to perform an action (example: backup)
"""

from nua.lib.panic import warning

from .app_instance import AppInstance
from .backup.backup_engine import backup_resource, backup_volume
from .backup.backup_report import global_backup_report
from .db import store
from .domain_split import DomainSplit
from .resource import Resource
from .volume import Volume


class AppManagement:
    """Management of a list of site."""

    def __init__(self):
        self.active_config = {}
        self.apps = []
        self.apps_per_domain = []
        # self.required_services = set()
        # self.available_services = {}

    def load_active_config(self) -> dict:
        """Return the current deployed configuration."""
        self.active_config = store.deploy_config_active()
        if not self.active_config:
            warning("The current deployed config is empty.")
            self.apps = []
            return
        self.apps = [
            AppInstance.from_dict(site_conf)
            for site_conf in self.active_config["deployed"]["apps"]
        ]

    def set_apps_per_domain(self):
        domains = {}
        for site in self.apps:
            dom_list = domains.setdefault(DomainSplit(site.domain), [])
            dom_list.append(site)
        self.apps_per_domain = [
            {"hostname": hostname, "apps": apps_list}
            for hostname, apps_list in domains.items()
        ]

    def do_full_backup(self, app: Resource) -> str:
        """Execute a full backup.

         backup order:
        1 - resources
        2 - app
        for each:
        a) backup tag of each volume
        b) backup tag of main resource
        """
        reports = []
        for resource in app.resources:
            reports.extend(self.do_backup(resource))
        reports.extend(self.do_backup(app))
        return global_backup_report(reports)

    def do_backup(self, resource: Resource) -> list:
        reports = []
        for volume_dict in resource.volume:
            volume = Volume.from_dict(volume_dict)
            reports.append(backup_volume(volume))
        reports.append(backup_resource(resource))
        return reports

    def backup_apps(self) -> str:
        """Execute a one-time backup for all site instance having a backup
        declaration."""
        self.load_active_config()
        result = []
        for app in self.apps:
            result.append(self.do_full_backup(app))
        return "\n".join(result)
