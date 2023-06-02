"""Base classe for backup plugins."""
import abc
from pathlib import Path
from typing import Any

from nua.lib.dates import backup_date

from ...resource import Resource
from ...volume import Volume
from ..backup_component import BackupComponent
from ..backup_report import BackupReport


class BackupErrorException(Exception):
    pass


class PluginBaseClass(abc.ABC):
    """Backup plugin base class.

    By default, the base class can apply to either Resource or Volume."""

    identifier = "plugin_identifier"

    def __init__(self, resource: Resource, volume: Volume | None = None):
        self.resource: Resource = resource
        self.volume: Volume | None = volume
        self.label: str = self.resource.label_id
        self.node: str = self.resource.container_name
        self.options: dict[str, Any] = {}
        if self.volume:
            backup_dict = self.volume.get("backup") or {}
        else:
            backup_dict = self.resource.get("backup") or {}
        self.options = backup_dict.get("options") or {}
        self.date: str = ""
        self.report: BackupReport = BackupReport(node=self.node, task=True)
        self.backup_folder: Path = Path()

    def restore(self) -> None:
        pass
        # restore_id = restore_fct_id("pg_dumpall")

    def make_nua_local_folder(self) -> None:
        """For local backup, make the destination local folder."""
        self.folder = Path("/home/nua/backups") / self.label / self.node / self.date
        self.folder.mkdir(exist_ok=True, parents=True)

    def set_date(self) -> None:
        self.date = backup_date()

    def base_name(self) -> str:
        return f"{self.date}-{self.node}"

    def do_backup(self) -> None:
        pass

    def finalize(self, file_name: str) -> None:
        self.report.message = file_name
        self.report.component = BackupComponent.generate(
            folder=str(self.folder),
            file_name=file_name,
            restore=self.identifier,
            date=self.date,
        )

    def run(self) -> BackupReport:
        """Backup the Resource or Volume.

        Returns:
            BackupReport instance
        """
        self.set_date()
        self.make_nua_local_folder()
        try:
            self.do_backup()
        except (BackupErrorException, RuntimeError) as e:
            self.report.message = f"Backup failed: {e}"
        else:
            self.report.success = True
        finally:
            print(self.report)
        return self.report
