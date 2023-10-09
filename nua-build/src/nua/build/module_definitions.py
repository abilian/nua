"""Parse content of definition modules.

Definitions are TOML descriptions of providers.
"""
from importlib import resources as rso
from pathlib import Path
from typing import Any

import tomli

MODULE_DEFINITIONS = {}


class ModuleDefinitions:
    DEFINITIONS_DIR = "nua.build.provider_modules"

    def register_definitions(self):
        for file in rso.files(self.DEFINITIONS_DIR).iterdir():
            with rso.as_file(file) as path:
                if path.suffix != ".toml" or path.stem.startswith("_"):
                    continue
                self._definitions_add(path)

    def _definitions_add(self, path: Path):
        content = tomli.loads(path.read_text(encoding="utf8"))
        MODULE_DEFINITIONS[content["module-name"]] = content

    @classmethod
    def module(cls, name: str) -> dict[str, Any] | None:
        module_definitions = cls()
        if not MODULE_DEFINITIONS:
            module_definitions.register_definitions()
        return MODULE_DEFINITIONS.get(name)
