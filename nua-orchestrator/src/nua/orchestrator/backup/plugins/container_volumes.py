"""Class to backup the volumes of a container."""
from docker.models.volumes import Volume as DockerVolume

from ...docker_utils import (
    docker_container_of_name,
    docker_container_volumes,
    docker_mount_point,
)
from ..backup_registry import register_plugin
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckContainerVolumes(PluginBaseClass):
    """Backup plugin to backup all volumes of a container.

    To be used at Resource level or AppInstance level.
    """

    identifier = "container_volumes"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Volumes of the Resource instance."""
        self.check_local_destination()

        container_name = self.node
        docker_volumes = docker_container_volumes(container_name)

        if not docker_volumes:
            raise BackupErrorException(
                f"Warning: No volume found for the container {self.node}"
            )

        for dock_volume in docker_volumes:
            self._backup_one_volume(dock_volume)

    def _backup_one_volume(self, dock_volume: DockerVolume):
        volume_name = dock_volume.name
        # volume_target =
        self.file_name = f"{self.date}-{volume_name}.tar.gz"
        dest_file = self.folder / self.file_name
        container = docker_container_of_name(self.node)
        if container is None:
            raise BackupErrorException(f"Error: No container found for {self.node}")

        mount_point = docker_mount_point(container, volume_name)
        if not mount_point:
            raise BackupErrorException(
                f"Error: No volume {volume_name} in its container"
            )

        cmd = f"tar cvzf {self.nua_backup_dir}/{self.file_name} {mount_point}"
        print(f"Start backup: {dest_file}")
        self.docker_run_ubuntu(cmd)
        self.volume_info = dock_volume.attrs
        self.finalize()


register_plugin(BckContainerVolumes)
