from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..cli import Config


@dataclass(frozen=True)
class Stage:
    config: Config
