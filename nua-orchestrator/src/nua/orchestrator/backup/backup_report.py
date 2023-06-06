from dataclasses import dataclass

from .backup_component import BackupComponent


@dataclass
class BackupReport:
    node: str = ""
    task: bool = False
    success: bool = False
    message: str = ""
    component: BackupComponent | None = None

    def __str__(self) -> str:
        if not self.task:
            return f"No backup task for {self.node}"
        if self.success:
            return f"Backup done for {self.node} to {self.message}"
        else:
            return f"Backup failed for {self.node}: {self.message}"
