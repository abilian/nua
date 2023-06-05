from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, kw_only=True)
class BackupComponent:
    """Single backup up unit (typically a directory or a database)
    and its restore method.

    One item has:
        - a path (or url)
        - a restore method (name of the backup plugin)
        - a backup date
    """

    folder: str = ""
    file_name: str = ""
    restore: str = ""
    date: str = ""
    volume_info: dict[str, Any] | None = None

    @classmethod
    def generate(
        cls,
        folder: str,
        file_name: str,
        restore: str,
        date: str,
        volume_info: dict[str, Any] | None,
    ) -> BackupComponent:
        component = BackupComponent(
            folder=folder,
            file_name=file_name,
            restore=restore,
            date=date,
            volume_info=volume_info,
        )
        component.save()
        return component

    @classmethod
    def from_dir(cls, folder: Path) -> BackupComponent:
        path = folder / "description.json"
        content = json.loads(path.read_text(encoding="utf8"))
        return BackupComponent(
            folder=content["folder"],
            file_name=content["file_name"],
            restore=content["restore"],
            date=content["date"],
            volume_info=content["volume_info"],
        )

    def save(self) -> None:
        path = Path(self.folder) / "description.json"
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=4),
            encoding="utf8",
        )
