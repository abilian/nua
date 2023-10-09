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

    To be used at Provider level or AppInstance level.
    """

    identifier = "tgz_volumes"

    def check_local_destination(self) -> None:
        backup_destination = self.options.get("destination", "local")
        if backup_destination == "local":
            return
        raise BackupErrorException("WIP: Only local backup is currently implemented")

    def do_backup(self) -> None:
        """Backup the Volumes of the Provider instance."""
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

        cmd = f"tar cvzf {self.nua_backup_dir}/{self.file_name} -C {mount_point} ."
        print(f"Start backup: {dest_file}")
        self.docker_run_ubuntu(cmd)
        self.volume_info = dock_volume.attrs
        self.finalize_component()

    def restore(self, component: BackupComponent) -> str:
        """Restore the Provider and or Volume."""
        volume_name = self._volume_name(component)
        mount_point = self._target_volume_mount_point(component, volume_name)
        bck_file = self.backup_file(component)
        return self._restore_volume(volume_name, mount_point, bck_file)

    def _volume_name(self, component) -> str:
        volume_info = component.volume_info
        if not volume_info:
            # this plugin only works with volumes
            raise RuntimeError("no volume info")
        return volume_info.get("Name", "")

    def _target_volume_mount_point(
        self,
        component: BackupComponent,
        volume_name: str,
    ) -> str:
        container = docker_container_of_name(self.node)
        if container is None:
            raise RuntimeError(f"Error: No container found for {self.node}")
        mount_point = docker_mount_point(container, volume_name)
        if not mount_point:
            raise RuntimeError(f"Error: No volume {volume_name} in container")
        return mount_point

    def _restore_volume(
        self,
        volume_name: str,
        mount_point: str,
        bck_file: Path,
    ) -> str:
        file_name = bck_file.name
        folder = str(bck_file.parent)
        bash_cmd = (
            f"cd {mount_point} && tar xvzf {self.nua_backup_dir}/{file_name} "
            # "--strip-components=1"
        )
        cmd = f"bash -c '{bash_cmd}'"
        print(f"Restore: {bck_file}")
        result = self.docker_run_ubuntu_restore(cmd, folder).strip().split("\n")
        txt_result = "    " + "\n    ".join(result)
        return txt_result


register_plugin(BckTgzVolumes)
