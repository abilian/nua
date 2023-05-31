from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BackupComponent:
    """Single backup up unit (typically a directory or a database)
    and its restore method.

    One item has:
        - a path (or url)
        - a restore method (name of the backup plugin)
        - a backup date
    """

    # container_name: str = ""
    path: str = ""
    restore: str = ""
    date: str = ""
