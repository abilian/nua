from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BackupItem:
    """Single backup up item (typically a file) and its restore method.

    One item has:
        - a path (or url)
        - a restore method
    """

    # container_name: str = ""
    path: str = ""
    restore: str = ""
