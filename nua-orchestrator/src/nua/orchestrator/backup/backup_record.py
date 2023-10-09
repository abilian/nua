from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

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
    ref_date: str = ""  # reference backup date
    date: str = ""  # datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    components: list[BackupComponent] = field(init=False, default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BackupRecord:
        record = cls(
            label_id=data["label_id"], date=data["date"], ref_date=data["ref_date"]
        )
        record.components = BackupComponent.from_dict_list(data)
        return record

    @property
    def date_time(self) -> datetime:
        return datetime.fromisoformat(self.date)

    def info(self) -> str:
        text = [
            f"label: {self.label_id}",
            f"reference: {self.ref_date}",
            f"date: {self.date}",
            "components:",
        ]
        for component in self.components:
            for txt in component.info_list():
                text.append(f"    {txt}")
            text.append("")
        return "\n".join(text)

    def as_dict(self) -> dict:
        return asdict(self)

    def append_component(self, component: BackupComponent):
        self.components.append(component)
