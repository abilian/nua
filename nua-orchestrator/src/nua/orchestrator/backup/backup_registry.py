"""Manage the available backup plugins."""
from collections.abc import Callable
from importlib import import_module
from importlib import resources as rso

BACKUP_PLUGINS: dict[str, Callable] = {}


def get_backup_plugin(identifier: str) -> Callable | None:
    if not BACKUP_PLUGINS or identifier not in BACKUP_PLUGINS:
        register_backup_plugins()
    return BACKUP_PLUGINS.get(identifier)


def register_backup_plugins():
    plugin_folder = "nua.orchestrator.backup.plugins"
    for file in rso.files(plugin_folder).iterdir():
        with rso.as_file(file) as path:
            if path.suffix != ".py" or path.stem.startswith("_"):
                continue
            import_module(f"{plugin_folder}.{path.stem}")


def register_plugin(cls: Callable) -> None:
    BACKUP_PLUGINS[cls.identifier] = cls
