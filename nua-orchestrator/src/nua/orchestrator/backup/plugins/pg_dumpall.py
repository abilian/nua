"""Class to backup a database."""
from pathlib import Path

from nua.lib.dates import backup_date

from ...docker_utils import docker_container_of_name, docker_exec_checked
from ...resource import Resource
from ...volume import Volume
from ..backup_record import BackupItem
from ..backup_registry import register_plugin
from ..backup_report import BackupReport


class BckPostgresDumpall:
    identifier = "pg_dumpall"

    def __init__(self, resource: Resource, volume: Volume | None = None):
        self.resource: Resource = resource
        self.volume: Volume = volume
        self.node: str = self.resource.container_name

    def restore(self) -> None:
        pass
        # restore_id = restore_fct_id("pg_dumpall")

    def backup(self) -> BackupReport:
        """Backup the Resource with pg_dumpall.

        Resource is expected to be a Postgres database.

        Returns:
            BackupReport instance
        """
        backup_conf = self.resource.get("backup")
        backup_destination = backup_conf.get("destination", "local")

        if backup_destination != "local":
            return BackupReport(
                node=self.node,
                task=True,
                success=False,
                message="WIP: Only local backup is currently implemented",
                backup_item=None,
            )
        # _backup_dir = store.installed_nua_settings()["backup"]["location"]
        file_name = f"{backup_date()}-{self.node}.sql"
        folder = Path("/home/nua/backups") / self.node
        folder.mkdir(exist_ok=True, parents=True)
        dest_file = folder / file_name
        container = docker_container_of_name(self.node)[0]
        cmd = "/usr/bin/pg_dumpall -U ${POSTGRES_USER}"

        print(f"Start backup: {dest_file}")
        report = BackupReport(node=self.node, task=True)
        try:
            with dest_file.open("wb") as output:
                docker_exec_checked(
                    container,
                    {"cmd": cmd, "user": "root", "workdir": "/"},
                    output,
                )
                output.flush()
        except RuntimeError as e:
            report.success = False
            report.message = f"Backup failed: {e}"
            report.backup_item = None
        else:
            backup_item = BackupItem(path=str(dest_file), restore=self.identifier)
            report.success = True
            report.message = (dest_file.name,)
            report.backup_item = backup_item
        finally:
            print(report)
            return report


register_plugin(BckPostgresDumpall)
