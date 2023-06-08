"""Class to backup the volumes of a container."""
from pathlib import Path

from docker.models.volumes import Volume as DockerVolume

from ...docker_utils import (
    docker_container_of_name,
    docker_container_volumes,
    docker_mount_point,
)
from ..backup_component import BackupComponent
from ..backup_registry import register_plugin
from ..backup_report import BackupReport
from .plugin_base_class import BackupErrorException, PluginBaseClass


class BckTgzVolumes(PluginBaseClass):
    """Backup plugin to backup all volumes of a container.

    To be used at Resource level or AppInstance level.
    """

    identifier = "tgz_volumes"

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
            self.report.success = True
            self.reports.append(self.report)

    def _backup_one_volume(self, dock_volume: DockerVolume):
        self.report = BackupReport(node=self.node, task=True)
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
        self.finalize_component()

    def restore(self, component: BackupComponent) -> str:
        """Restore the Resource and or Volume."""
        print("restore()")
        container_name = self.node

        docker_volumes = docker_container_volumes(container_name)
        volume_info = component.volume_info
        if not volume_info:
            # this plugin only works with volumes
            return "no volume info"
        print(volume_info)
        volume_name = volume_info.get("Name", "")
        docker_volumes = docker_container_volumes(container_name)
        if not docker_volumes:
            raise RuntimeError(
                f"Warning: No volume found for the container {self.node}"
            )
        target_volume = None
        for dock_volume in docker_volumes:
            if dock_volume.name == volume_name:
                target_volume = dock_volume
                break
        if not target_volume:
            raise RuntimeError(f"Warning: No volume {volume_name}")
        bck_file = Path(component.folder) / component.file_name
        if not bck_file.exists():
            raise RuntimeError(f"Warning: No backup file {bck_file}")
        print(bck_file)
        return self._restore_volume(target_volume, bck_file)

    def _restore_volume(self, dock_volume: DockerVolume, bck_file: Path) -> str:
        container = docker_container_of_name(self.node)
        if container is None:
            raise RuntimeError(f"Error: No container found for {self.node}")
        volume_name = dock_volume.name
        # volume_target =
        mount_point = docker_mount_point(container, volume_name)
        if not mount_point:
            raise RuntimeError(f"Error: No volume {volume_name} in container")
        file_name = bck_file.name
        folder = str(bck_file.parent)
        bash_cmd = (
            f"cd {mount_point} && tar xvzf {self.nua_backup_dir}/{file_name} --strip 1"
        )
        cmd = f"bash -c '{bash_cmd}'"
        print(f"Start restore: {bck_file}")
        print(cmd)
        result = self.docker_run_ubuntu_restore(cmd, folder).decode("utf8")
        print("run result:", result)
        return result


register_plugin(BckTgzVolumes)
