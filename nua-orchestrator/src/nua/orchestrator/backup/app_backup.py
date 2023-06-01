from dataclasses import dataclass, field
from datetime import datetime, timezone
from pprint import pformat

from nua.lib.panic import vprint, warning
from nua.lib.tool.state import verbosity

from ..app_instance import AppInstance
from ..resource import Resource
from ..volume import Volume
from .backup_record import BackupRecord
from .backup_report import BackupReport
from .resource_backup import backup_resource
from .volume_backup import backup_volume


@dataclass
class AppBackup:
    """Class to control the backup of an app and its volumes."""

    app: AppInstance
    reports: list[BackupReport] = field(init=False, default_factory=list)
    result: str = ""
    success: bool = False

    def run(self):
        for resource in self.app.resources:
            self._backup_resource_parts(resource)
        self._backup_resource_parts(self.app)
        self._summarize()
        self._store_in_app()

    def _backup_resource_parts(self, resource: Resource):
        for volume_dict in resource.volumes:
            volume = Volume.from_dict(volume_dict)
            self.reports.append(backup_volume(resource, volume))
        self.reports.append(backup_resource(resource))

    def _summarize(self):
        if any(report.task for report in self.reports):
            if all(report.success for report in self.reports if report.task):
                self.result = f"Backup tasks successful for {self.app.container_name}"
                self.success = True
            else:
                self._failed_result()
                self.success = False
        else:
            self.result = f"No backup task for {self.app.container_name}"
            self.success = True

    def _failed_result(self) -> None:
        result = ["Some task did fail:"]
        success_str = {True: "succeed", False: "failed"}
        for report in self.reports:
            if not report.task:
                continue
            result.append(
                f"  {report.node}, {success_str[report.success]}: {report.message}"
            )
        self.result = "\n".join(result)

    def _make_backup_record(self) -> BackupRecord:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        record = BackupRecord(label_id=self.app.label_id, date=now)
        for report in self.reports:
            if report.task and report.success and report.component is not None:
                record.append_component(report.component)
        return record

    def _store_in_app(self):
        if not self.success:
            warning("Backup unsuccessful: not stored in app valid backups")
            return
        record = self._make_backup_record()
        with verbosity(2):
            vprint(pformat(record.as_dict()))
        self.app.backup_records.append(record.as_dict())
