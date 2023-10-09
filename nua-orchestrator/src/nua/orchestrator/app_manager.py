"""class to manage the currently active apps.

General use:
    - load active configuration
    - loop over apps to perform an action (example: backup)
"""

from nua.lib.docker import docker_sanitized_name
from nua.lib.panic import Abort, vprint, warning
from nua.lib.tool.state import verbosity

from .app_instance import AppInstance
from .backup.app_backup import AppBackup
from .backup.app_restore import AppRestore
from .db import store
from .domain_split import DomainSplit
from .provider import Provider
from .volume import Volume


class AppManager:
    """Management of a list of site."""

    def __init__(self):
        self.active_config = {}
        self.active_config_loaded = False
        self.apps = []
        self.previous_config_id = 0

    def instances_of_domain(self, domain: str) -> list[AppInstance]:
        """Select deployed instances of domain."""
        self.load_active_config()
        if app_list := self.apps_per_domain().get(domain):
            return app_list
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
            self.previous_config_id = self.active_config.get("id", 0)
            self.apps = [
                AppInstance.from_dict(site_conf)
                for site_conf in self.active_config["deployed"]["apps"]
            ]
        else:
            warning("The current deployed config is empty.")
            self.apps = []
        self.active_config_loaded = True

    def apps_per_domain(self) -> dict[str, list]:
        domains = {}
        for app in self.apps:
            dom_list = domains.setdefault(DomainSplit(app.domain).hostname, [])
            dom_list.append(app)
        return domains

    def backup_all_apps(self) -> str:
        """Execute a one-time backup for all site instance having a backup
        declaration."""
        self.load_active_config()
        return self._backup_apps(self.apps)

    def backup_app_domain(self, domain: str) -> str:
        """Execute a one-time backup for the apps instance of domain."""
        return self._backup_apps(self.instances_of_domain(domain))

    def _backup_apps(self, apps: list[AppInstance]) -> str:
        """Execute a one-time backup for list of apps."""
        results = [self.backup_one_app(app) for app in apps]
        return "\n".join(results)

    def backup_app_label(self, label: str) -> str:
        """Execute a one-time backup for the app instance."""
        app = self.instance_of_label(label)
        return self.backup_one_app(app)

    def backup_one_app(self, app: AppInstance) -> str:
        """Execute a full backup of an app (all volumes).

        Backup order:
        1 - providers of app
        2 - app
        for each:
            a) backup tag of each volume
            b) backup tag of main provider
        """
        app_backup = AppBackup(app)
        app_backup.run()
        if app_backup.success:
            self._store_app_instance(app)
        return app_backup.result

    def _store_app_instance(self, app: AppInstance):
        with verbosity(3):
            vprint("Saving AppInstance configuration in Nua DB")
        store.store_instance(
            app_id=app.app_id,
            label_id=app.label_id,
            nua_tag=app.nua_tag,
            domain=app.domain,
            container=app.container_name,
            image=app.image,
            state=app.running_status,
            site_config=dict(app),
        )

    def restore_backup_app_per_label(self, label: str) -> str:
        """Execute a backup restoration.

        It is assumed that the app is stopped."""
        app = self.instance_of_label(label)
        app_restore = AppRestore(app)
        app_restore.run(reference="")
        if app_restore.success:
            self._store_app_instance(app)
        return app_restore.result
        # return global_backup_report(reports)

    def restore_backup_app_per_domain(self, domain: str) -> None:
        """Execute a backup restoration.

        It is assumed that the app is stopped."""
        print("WIP, nothing")

    def do_restore(self, provider: Provider) -> list:
        reports = []
        for volume_dict in provider.volumes:
            volume = Volume.from_dict(volume_dict)
            # reports.append(backup_volume(volume))
            print("WIP pseudo restore", volume)
        print("WIP pseudo restore", provider.provider_name, provider.container_name)
        # reports.append(backup_provider(provider))
        return reports

    def restore_list_backups_app_per_label(self, label: str) -> str:
        """List available backups for the app."""
        app = self.instance_of_label(label)
        text = [bck_record.info() for bck_record in app.backup_records_objects]
        return "\n\n".join(text)

    def restore_list_backups_app_per_domain(self, domain: str) -> str:
        """List available backups for the app."""
        return "WIP, nothing"
