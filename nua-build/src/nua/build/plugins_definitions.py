"""Parse content of definition plugins.

Definitions are TOML descriptions of resources.
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
        plugin = content["plugin"]
        PLUGIN_DEFINITIONS[plugin["name"]] = content

    @classmethod
    def plugin(cls, name: str) -> dict[str, Any] | None:
        plugin_definitions = cls()
        if not PLUGIN_DEFINITIONS:
            plugin_definitions.register_definitions()
        return PLUGIN_DEFINITIONS.get(name)


# def _is_family_plugins(name: str, family: str) -> bool:
#     return any_hyphen_in(FAMILY_SET.get(family, set()), name)


# def is_db_plugins(name: str) -> bool:
#     return _is_family_plugins(name, "db")


# def is_docker_plugin(name: str) -> bool:
#     return any_hyphen_in(DOCKER_MODULES, name)


# def is_assignable_plugin(name: str) -> bool:
#     return any_hyphen_in(ASSIGN_MODULES, name)


# def is_network_plugin(name: str) -> bool:
#     return any_hyphen_in(NETWORK_MODULES, name)
