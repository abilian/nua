"""class to manage the currently active apps.

General use:
    - load active configuration
    - loop over apps to perform an action (example: backup)
"""


from nua.lib.docker import docker_sanitized_name
from nua.lib.panic import Abort, warning

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
        self.active_config_loaded = False
        self.apps = []
        self.apps_per_domain = []
        # self.required_services = set()
        # self.available_services = {}

    def backup_apps(self) -> str:
        """Execute a one-time backup for all site instance having a backup
        declaration."""
        self.load_active_config()
        result = []
        for app in self.apps:
            result.append(self.do_full_backup(app))
        return "\n".join(result)

    def instances_of_domain(self, domain: str) -> list[AppInstance]:
        """Select deployed instances of domain."""
        self.load_active_config()
        for apps_dom in self.apps_per_domain:
            if apps_dom["hostname"] == domain:
                return apps_dom["apps"]
        raise Abort(f"No instance found for domain '{domain}'")

    def instance_of_label(self, label: str) -> AppInstance:
        """Select deployed instances per label."""
        label_id = docker_sanitized_name(label)
        self.load_active_config()
        for app in self.apps:
            if app.label_id == label_id:
                return app
        raise Abort(f"No instance found for label_id '{label_id}'")

    def load_active_config(self) -> None:
        """Return the current deployed configuration."""
        if self.active_config_loaded:
            return
        self.active_config = store.deploy_config_active()
        if self.active_config:
            self.apps = [
                AppInstance.from_dict(site_conf)
                for site_conf in self.active_config["deployed"]["apps"]
            ]
        else:
            warning("The current deployed config is empty.")
            self.apps = []
        self.active_config_loaded = True

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
        """Execute a full backup of an app (all volumes).

        Backup order:
        1 - resources of app
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

    def restore_app_label(self, label: str):
        """Execute a backup restoration.

        It is assumed that the app is stopped."""
        app = self.instance_of_label(label)
        reports = []
        for resource in app.resources:
            reports.extend(self.do_restore(resource))
        reports.extend(self.do_restore(app))
        # return global_backup_report(reports)

    def do_restore(self, resource: Resource) -> list:
        reports = []
        for volume_dict in resource.volume:
            volume = Volume.from_dict(volume_dict)
            # reports.append(backup_volume(volume))
            print("WIP pseudo restore", volume)
        print("WIP pseudo restore", resource.resource_name, resource.container_name)
        # reports.append(backup_resource(resource))
        return reports

    def restore_app_domain(self, domain: str):
        """Execute a backup restoration.

        It is assumed that the app is stopped."""
        print("WIP, nothing")
