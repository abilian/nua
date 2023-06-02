from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


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

    @classmethod
    def generate(
        cls, folder: str, file_name: str, restore: str, date: str
    ) -> BackupComponent:
        component = BackupComponent(
            folder=folder, file_name=file_name, restore=restore, date=date
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
        )

    def save(self) -> None:
        path = Path(self.folder) / "description.json"
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=4),
            encoding="utf8",
        )
