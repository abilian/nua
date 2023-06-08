"""Class to backup a Mariadb database."""


from ...docker_utils import docker_container_of_name, docker_exec_checked
from ..backup_registry import register_plugin
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckMysqldump(PluginBaseClass):
    """Backup plugin for MariaDB Docker container using mysqldump.

    To be used at Resource level, on a MariaDB container.
    """

    identifier = "mysqldump"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Resource with mysqldump.

        Resource is expected to be a MariaDB database.
        """
        self.check_local_destination()

        self.file_name = f"{self.date}-{self.node}.sql"
        dest_file = self.folder / self.file_name

        container = docker_container_of_name(self.node)
        if container is None:
            raise BackupErrorException(f"Error: No container found for {self.node}")

        cmd = "mysqldump -U -p${MARIADB_ROOT_PASSWORD} --all-databases"

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


register_plugin(BckMysqldump)
