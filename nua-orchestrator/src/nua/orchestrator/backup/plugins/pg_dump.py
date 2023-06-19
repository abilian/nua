"""Class to backup a database."""


from ...docker_utils import (
    docker_container_of_name,
    docker_exec_checked,
    docker_exec_stdin,
)
from ..backup_component import BackupComponent
from ..backup_registry import register_plugin
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckPostgresDump(PluginBaseClass):
    """Backup plugin for Postgres Docker continaer using pg_dumpall.

    To be used at Provider level, on a Postgres container.
    """

    identifier = "pg_dump"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Provider with pg_dumpall.

        Provider is expected to be a Postgres database.
        """
        self.check_local_destination()

        self.file_name = f"{self.date}-{self.node}.sql"
        dest_file = self.folder / self.file_name

        container = docker_container_of_name(self.node)
        if container is None:
            raise BackupErrorException(f"Error: No container found for {self.node}")

        cmd = "/usr/bin/pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB}  --clean"

        print(f"Start backup: {dest_file}")
        with dest_file.open("wb") as output:
            docker_exec_checked(
                container,
                {"cmd": cmd, "user": "root", "workdir": "/"},
                output,
            )
            output.flush()
        self.finalize_component()
        self.report.success = True
        self.reports.append(self.report)

    def restore(self, component: BackupComponent) -> str:
        """Restore the Provider."""
        container = docker_container_of_name(self.node)
        bck_file = self.backup_file(component)
        bash_cmd = (
            r"PGOPTIONS='--client-min-messages=warning' /usr/bin/psql -q "
            "-U '${POSTGRES_USER}' -d '${POSTGRES_DB}'"
        )
        cmd = f"bash -c '{bash_cmd}'"
        print(f"Restore: {bck_file}")
        result = docker_exec_stdin(container, cmd, bck_file).strip()
        return result or "    done"


register_plugin(BckPostgresDump)
