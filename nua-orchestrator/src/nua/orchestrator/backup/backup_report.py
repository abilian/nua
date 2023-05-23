from dataclasses import dataclass

from .backup_record import BackupItem


@dataclass
class BackupReport:
    node: str = ""
    task: bool = False
    success: bool = True
    message: str = ""
    backup_item: BackupItem | None = None

    def __str__(self) -> str:
        if self.success:
            return f"Backup done for {self.node} to {self.message}"
        else:
            return f"Backup failed for {self.node}: {self.message}"
