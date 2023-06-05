"""Class to backup locally a directory."""


from nua.lib.exec import exec_as_root

from ...docker_utils import docker_container_named_volume
from ..backup_registry import register_plugin
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckLocalTar(PluginBaseClass):
    """Backup plugin for local directory.

    To be used at Volume level.
    """

    identifier = "tar"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Resource with tar  (test)."""
        self.check_local_destination()

        file_name = f"{self.base_name()}.tar.gz"
        dest_file = self.folder / file_name
        docker_volume = docker_container_named_volume(self.node, self.volume.full_name)
        if docker_volume is None:
            raise BackupErrorException(
                f"Error: No container/volume found for {self.node}/{self.volume.full_name}"
            )

        self.volume_info = docker_volume.attrs
        source = self.volume_info["Mountpoint"]
        cmd = f"tar czf {dest_file} {source}"
        print(f"Start backup: {dest_file}")
        exec_as_root(cmd)
        self.finalize(file_name)


register_plugin(BckLocalTar)
