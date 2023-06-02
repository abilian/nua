"""Class to backup a database."""


from ...docker_utils import docker_container_of_name, docker_exec_checked
from ..backup_registry import register_plugin
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckPostgresDumpall(PluginBaseClass):
    """Backup plugin for Postgres Docker continaer using pg_dumpall.

    To be used at Resource level, on a Postgres container.
    """

    identifier = "pg_dumpall"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Resource with pg_dumpall.

        Resource is expected to be a Postgres database.

        Returns:
            BackupReport instance
        """
        self.check_local_destination()

        file_name = f"{self.base_name()}.sql"
        dest_file = self.folder / file_name

        container = docker_container_of_name(self.node)
        if container is None:
            raise BackupErrorException(f"Error: No container found for {self.node}")

        cmd = "/usr/bin/pg_dumpall -U ${POSTGRES_USER}"

        print(f"Start backup: {dest_file}")
        with dest_file.open("wb") as output:
            docker_exec_checked(
                container,
                {"cmd": cmd, "user": "root", "workdir": "/"},
                output,
            )
            output.flush()
        self.finalize(file_name)


register_plugin(BckPostgresDumpall)
