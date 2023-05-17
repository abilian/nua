from dataclasses import asdict, dataclass, field
from pprint import pformat

from nua.lib.dates import backup_date
from nua.lib.panic import vprint, warning
from nua.lib.tool.state import verbosity

from ..app_instance import AppInstance
from ..resource import Resource
from ..volume import Volume
from .backup_engine import backup_resource, backup_volume
from .backup_record import BackupItem
from .backup_report import BackupReport


@dataclass(kw_only=True)
class BackupRecord:
    """Record of a successful backup of the data of an instance.

    One record has
      - a unique reference date (start date)
      - a list of backuped items and their restore method

    wip: maybe store start/end date of backup for long duration backups
    """

    label_id: str = ""
    ref_date: str = ""
    items: list[BackupItem] = field(init=False, default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def append_item(self, backup_item: BackupItem):
        self.items.append(backup_item)


@dataclass
class AppBackup:
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
        for volume_dict in resource.volume:
            volume = Volume.from_dict(volume_dict)
            self.reports.append(backup_volume(volume))
        self.reports.append(backup_resource(resource))

    def _summarize(self):
        if any(rep.task for rep in self.reports):
            if all(rep.success for rep in self.reports if rep.task):
                self.result = f"Backup tasks successful for {self.app.container_name}"
                self.success = True
            else:
                self._failed_result()
                self.success = False
        else:
            self.result = f"No backup task for {self.app.container_name}"
            self.success = True

    def _failed_result(self) -> str:
        result = ["Some task did fail:"]
        success_str = {True: "succeed", False: "failed"}
        for rep in self.reports:
            if not rep.task:
                continue
            result.append(f"  {rep.node}, {success_str[rep.success]}: {rep.message}")
        self.result = "\n".join(result)

    def _store_in_app(self):
        if not self.success:
            warning("Backup unsuccessful: not stored in app valid backups")
            return
        # maybe datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        record = BackupRecord(label_id=self.app.label_id, ref_date=backup_date())
        for rep in self.reports:
            if rep.task and rep.success and rep.backup_item is not None:
                record.append_item(rep.backup_item)
        with verbosity(2):
            vprint(pformat(record.as_dict()))
        self.app.backup_records.append(record.as_dict())
