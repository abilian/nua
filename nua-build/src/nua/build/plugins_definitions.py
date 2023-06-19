"""Parse content of definition plugins.

Definitions are TOML descriptions of providers.
"""
from importlib import resources as rso
from pathlib import Path
from typing import Any

import tomli

PLUGIN_DEFINITIONS = {}


class PluginDefinitions:
    DEFINITIONS_DIR = "nua.build.definitions"

    def register_definitions(self):
        for file in rso.files(self.DEFINITIONS_DIR).iterdir():
            with rso.as_file(file) as path:
                if path.suffix != ".toml" or path.stem.startswith("_"):
                    continue
                self._definitions_add(path)

    def _definitions_add(self, path: Path):
        content = tomli.loads(path.read_text(encoding="utf8"))
        PLUGIN_DEFINITIONS[content["plugin-name"]] = content

    @classmethod
    def plugin(cls, name: str) -> dict[str, Any] | None:
        plugin_definitions = cls()
        if not PLUGIN_DEFINITIONS:
            plugin_definitions.register_definitions()
        return PLUGIN_DEFINITIONS.get(name)
