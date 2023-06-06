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
    def from_dir(cls, folder: Path | str) -> list[BackupComponent]:
        path = Path(folder) / "description.json"
        if not path.is_file():
            return []
        content = json.loads(path.read_text(encoding="utf8"))
        components_json = content.get("component") or []
        components = [
            BackupComponent(
                folder=item["folder"],
                file_name=item["file_name"],
                restore=item["restore"],
                date=item["date"],
                volume_info=item["volume_info"],
            )
            for item in components_json
        ]
        return components

    def save(self) -> None:
        bc_list = BackupComponent.from_dir(self.folder)
        bc_list.append(self)
        content = {"component": [asdict(bc) for bc in bc_list]}
        path = Path(self.folder) / "description.json"
        path.write_text(
            json.dumps(content, ensure_ascii=False, indent=4),
            encoding="utf8",
        )
