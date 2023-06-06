"""Class to backup a MongoDB database."""


from ...docker_utils import docker_container_of_name, docker_exec_checked
from ..backup_registry import register_plugin
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckMongodump(PluginBaseClass):
    """Backup plugin for MongoDB Docker container using mongodump.

    To be used at Resource level, on a MongoDB container.
    """

    identifier = "mongodump"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Resource with mongodump.

        Resource is expected to be a mongodump database.
        """
        self.check_local_destination()

        self.file_name = f"{self.date}-{self.node}.archive"
        dest_file = self.folder / self.file_name

        container = docker_container_of_name(self.node)
        if container is None:
            raise BackupErrorException(f"Error: No container found for {self.node}")

        cmd = (
            "/usr/bin/mongodump -u ${MONGO_INITDB_ROOT_USERNAME} "
            "-p ${MONGO_INITDB_ROOT_PASSWORD} --archive"
        )

        print(f"Start backup: {dest_file}")
        with dest_file.open("wb") as output:
            docker_exec_checked(
                container,
                {"cmd": cmd, "user": "root", "workdir": "/"},
                output,
            )
            output.flush()
        self.finalize()


register_plugin(BckMongodump)
