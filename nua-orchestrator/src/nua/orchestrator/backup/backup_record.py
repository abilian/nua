from dataclasses import asdict, dataclass, field


@dataclass(frozen=True, kw_only=True)
class BackupItem:
    """Single backuped item (a file).

    One item has:
        - a path (or url)
        - a restore method
        # - a container reference ?
    """

    # container_name: str = ""
    path: str = ""
    restore: str = ""


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
