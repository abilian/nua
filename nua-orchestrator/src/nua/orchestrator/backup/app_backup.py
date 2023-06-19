from dataclasses import dataclass, field
from datetime import datetime, timezone
from pprint import pformat

from nua.lib.dates import backup_date
from nua.lib.panic import vprint, warning
from nua.lib.tool.state import verbosity

from ..app_instance import AppInstance
from ..provider import Provider
from ..volume import Volume
from .backup_record import BackupRecord
from .backup_report import BackupReport
from .provider_backup import backup_provider
from .volume_backup import backup_volume


@dataclass
class AppBackup:
    """Class to control the backup of an app and its volumes."""

    app: AppInstance
    reports: list[BackupReport] = field(init=False, default_factory=list)
    result: str = ""
    detailed_result: str = ""
    success: bool = False
    ref_date: str = ""

    def run(self):
        self.ref_date = backup_date()
        for provider in self.app.providers:
            self._backup_provider_parts(provider)
        self._backup_provider_parts(self.app)
        self._summarize()
        self._make_detailed_result()
        self._store_in_app()

    def _backup_provider_parts(self, provider: Provider) -> None:
        # with verbosity(3):
        #     print("_backup_provider_parts()", provider.container_name)
        for volume_dict in provider.volumes:
            volume = Volume.from_dict(volume_dict)
            report = backup_volume(provider, volume, ref_date=self.ref_date)
            if report.task:
                with verbosity(2):
                    print(report)
            self.reports.append(report)
        reports = backup_provider(provider, ref_date=self.ref_date)
        # with verbosity(2):
        #     print(reports)
        self.reports.extend(reports)

    def _summarize(self) -> None:
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

    def _make_detailed_result(self) -> None:
        self.detailed_result = "\n".join(
            str(report) for report in self.reports if report.task
        )

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
        record = BackupRecord(
            label_id=self.app.label_id, ref_date=self.ref_date, date=now
        )
        for report in self.reports:
            if report.task and report.success and report.component is not None:
                record.append_component(report.component)
        return record

    def _store_in_app(self) -> None:
        # with verbosity(1):
        #     vprint(self.detailed_result)
        if not self.success:
            warning("Backup unsuccessful: not stored in app valid backups")
            return
        record = self._make_backup_record()
        with verbosity(2):
            vprint(pformat(record.as_dict()))
        self.app.backup_records.append(record.as_dict())
        self.app.backup_records_crop()
