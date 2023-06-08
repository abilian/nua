from dataclasses import dataclass
from ..resource import Resource

from ..app_instance import AppInstance
from .backup_component import BackupComponent
from .backup_record import BackupRecord
from .backup_registry import get_backup_plugin


@dataclass
class AppRestore:
    """Class to control the restoration from backup of an app instance."""

    app: AppInstance
    backup_record: BackupRecord | None = None
    result: str = ""
    detailed_result: str = ""
    success: bool = False

    def run(self, reference: str) -> None:
        """Restore the backup of reference date 'reference'.

        If reference is rempty, restore the last known backup."""
        self.load_backup_record(reference)
        if not self.backup_record:
            self.result = "No backup archive found."
            return
        try:
            self.restore_from_recorded_backup()
        except RuntimeError:
            return
        # self._summarize()

    def load_backup_record(self, reference: str) -> None:
        self.backup_record = None
        records = self.app.backup_records_objects
        if not records:
            return
        if reference:
            for record in records:
                if record.ref_date == reference:
                    self.backup_record = record
                    return
            return
        self.backup_record = records[-1]

    def restore_from_recorded_backup(self) -> None:
        """Restore volumes from recorded list of backup components."""
        if self.backup_record is None:
            return
        for component in self.backup_record.components:
            self.result += self.restore_component(component)
            self.result += "\n"

    def resource_from_container_name(self, container_name: str) -> Resource:
        if self.app.container_name == container_name:
            return self.app
        for resource in self.app.resources:
            if resource.container_name == container_name:
                return resource
        self.result = f"Unknown container '{container_name}'"
        raise RuntimeError

    def restore_component(self, component: BackupComponent) -> str:
        resource = self.resource_from_container_name(
            component.resource_info.get("container_name", "")
        )
        method = component.restore
        print("component:", method)
        backup_class = get_backup_plugin(method)
        print(backup_class)
        if backup_class is None:
            message = f"Unknown backup method '{method}'"
            self.result = message
            print(message)
            raise RuntimeError
        restorator = backup_class(resource)
        print(restorator)
        return restorator.restore(component)
