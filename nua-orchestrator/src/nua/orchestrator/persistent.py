from __future__ import annotations

from copy import deepcopy
from pprint import pformat
from typing import Any


class Persistent:
    """Management of persistent generated values (like passwords)."""

    def __init__(self, name: str):
        self.name = name
        self._dict = {}

    @classmethod
    def from_name_dict(cls, name: str, persist_dict: dict) -> Persistent:
        persistent = cls(name)
        persistent._dict.update(persist_dict)
        return persistent

    def as_dict(self):
        return {self.name: deepcopy(self._dict)}

    def __str__(self) -> str:
        return pformat(self._dict)

    def __setitem__(self, key: str, item: Any):
        self._dict[key] = item

    def __getitem__(self, key: str) -> Any:
        return self._dict[key]

    def has_key(self, key: str) -> bool:
        return key in self._dict

    def get(self, key: str, default=None) -> Any:
        return self._dict.get(key, default)

    def delete(self, key: str) -> None:
        if key in self._dict:
            del self._dict[key]