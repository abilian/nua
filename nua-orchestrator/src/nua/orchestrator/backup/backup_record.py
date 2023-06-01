from dataclasses import asdict, dataclass, field

from .backup_component import BackupComponent


@dataclass(kw_only=True)
class BackupRecord:
    """Record of a successful backup of the data of an instance.

    One record:
      - label_id of the app
      - unique reference date (end date, iso format)
      - list of backuped components and their restore method
    """

    label_id: str = ""
    date: str = ""  # datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    components: list[BackupComponent] = field(init=False, default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def append_component(self, component: BackupComponent):
        self.components.append(component)
