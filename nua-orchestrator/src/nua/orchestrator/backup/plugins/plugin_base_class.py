"""Base classe for backup plugins."""
import abc
from pathlib import Path
from typing import Any

import docker
from nua.lib.dates import backup_date
from nua.lib.docker import docker_require

from ...provider import Provider
from ...volume import Volume
from ..backup_component import BackupComponent
from ..backup_report import BackupReport

BACKUP_CONTAINER = "ubuntu:jammy-20230425"


class BackupErrorException(Exception):
    pass


class PluginBaseClass(abc.ABC):
    """Backup plugin base class.

    By default, the base class can apply to either Provider or Volume."""

    identifier = "plugin_identifier"
    nua_backup_dir = "/nua_backup_dir"

    def __init__(
        self,
        provider: Provider,
        volume: Volume | None = None,
        ref_date: str = "",
    ):
        self.provider: Provider = provider
        self.volume: Volume | None = volume
        self.volume_info: dict[str, Any] | None = None
        self.label: str = self.provider.label_id
        self.node: str = self.provider.container_name
        self.options: dict[str, Any] = {}
        if self.volume:
            backup_dict = self.volume.get("backup") or {}
        else:
            backup_dict = self.provider.get("backup") or {}
        self.options = backup_dict.get("options") or {}
        self.date: str = ref_date
        self.report: BackupReport = BackupReport(node=self.node, task=True)
        self.reports: list[BackupReport] = []
        self.folder: Path = Path()
        self.file_name: str = ""

    def restore(self, component: BackupComponent) -> str:
        """Restore the Provider and or Volume. To be implemented by sub class."""
        message = "NotImplemented"
        print(message)
        return message

    def make_nua_local_folder(self) -> None:
        """For local backup, make the destination local folder."""
        self.folder = Path("/home/nua/backups") / self.label / self.date
        self.folder.mkdir(exist_ok=True, parents=True)

    def set_date(self) -> None:
        if not self.date:
            self.date = backup_date()

    def docker_run_ubuntu(self, command: str) -> str:
        docker_require(BACKUP_CONTAINER)
        client = docker.DockerClient.from_env()
        return client.containers.run(
            BACKUP_CONTAINER,
            command=command,
            # mounts=
            remove=True,
            detach=False,
            stream=False,
            volumes_from=[self.node],
            volumes={str(self.folder): {"bind": self.nua_backup_dir, "mode": "rw"}},
        )

    def docker_run_ubuntu_restore(self, command: str, bck_folder: str) -> str:
        docker_require(BACKUP_CONTAINER)
        client = docker.DockerClient.from_env()
        result = client.containers.run(
            BACKUP_CONTAINER,
            command=command,
            # mounts=
            remove=True,
            detach=False,
            stream=False,
            volumes_from=[self.node],
            volumes={bck_folder: {"bind": self.nua_backup_dir, "mode": "rw"}},
        )
        return result.decode("utf8")

    def do_backup(self) -> None:
        """To be implemented by sub class"""
        raise NotImplementedError

    def finalize_component(self) -> None:
        self.report.message = self.file_name
        self.report.component = BackupComponent.generate(
            folder=str(self.folder),
            file_name=self.file_name,
            restore=self.identifier,
            date=self.date,
            provider_info={
                "label_id": self.provider.label_id,
                "container_name": self.provider.container_name,
                # "domain": self.provider.domain,
            },
            volume_info=self.volume_info,
        )

    def backup_file(self, component: BackupComponent) -> Path:
        bck_file = Path(component.folder) / component.file_name
        if not bck_file.exists():
            raise RuntimeError(f"Warning: No backup file {bck_file}")
        return bck_file

    def run(self) -> BackupReport:
        """Backup the Provider or Volume."""
        self.set_date()
        self.make_nua_local_folder()
        try:
            self.do_backup()
        except (BackupErrorException, RuntimeError) as e:
            self.report.message = f"Backup failed: {e}"
        else:
            self.report.success = True
        finally:
            pass
            # print(self.report)
        return self.report

    def run_on_provider(self) -> list[BackupReport]:
        """Backup the Volumes of the provider."""
        self.set_date()
        self.make_nua_local_folder()
        self.reports = []
        try:
            self.do_backup()
        except (BackupErrorException, RuntimeError) as e:
            self.report.message = f"Backup failed: {e}"
            self.reports.append(self.report)
        finally:
            pass
            # print(self.report)
        return self.reports
