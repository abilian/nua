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
    provider_info: dict[str, Any] | None = None
    volume_info: dict[str, Any] | None = None

    def info_list(self) -> list[str]:
        text = [
            # f"backup_date: {self.date}",
            f"method: {self.restore}",
            f"file name: {self.file_name}",
        ]
        if self.provider_info:
            container_name = self.provider_info.get("container_name", "")
            if container_name:
                text.append(f"container name: {container_name}")
            # domain = self.provider_info.get("domain", "")
            # if domain:
            #     text.append(f"domain: {domain}")
        if self.volume_info:
            name = self.volume_info.get("Name", "")
            if name:
                text.append(f"name: {name}")
            # mount = self.volume_info.get("Mountpoint", "")
            # if mount:
            #     text.append(f"mount point: {mount}")
        return text

    @classmethod
    def generate(
        cls,
        folder: str,
        file_name: str,
        restore: str,
        date: str,
        provider_info: dict[str, Any] | None,
        volume_info: dict[str, Any] | None,
    ) -> BackupComponent:
        component = BackupComponent(
            folder=folder,
            file_name=file_name,
            restore=restore,
            date=date,
            provider_info=provider_info,
            volume_info=volume_info,
        )
        component.save()
        return component

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> BackupComponent:
        return cls(
            folder=item["folder"],
            file_name=item["file_name"],
            restore=item["restore"],
            date=item["date"],
            provider_info=item["provider_info"],
            volume_info=item["volume_info"],
        )

    @classmethod
    def from_dict_list(cls, content: dict[str, Any]) -> list[BackupComponent]:
        components_json = content.get("components") or []
        return [BackupComponent.from_dict(item) for item in components_json]

    @classmethod
    def from_dir(cls, folder: Path | str) -> list[BackupComponent]:
        path = Path(folder) / "description.json"
        if not path.is_file():
            return []
        content = json.loads(path.read_text(encoding="utf8"))
        return BackupComponent.from_dict_list(content)

    def save(self) -> None:
        bc_list = BackupComponent.from_dir(self.folder)
        bc_list.append(self)
        content = {"component": [asdict(bc) for bc in bc_list]}
        path = Path(self.folder) / "description.json"
        path.write_text(
            json.dumps(content, ensure_ascii=False, indent=4),
            encoding="utf8",
        )
