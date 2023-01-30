"""Parse content of db_plugins

Family "db" can have functions:
    - configure_db()
    - setup_db()
"""
import importlib.util
from collections.abc import Callable
from importlib import resources as rso
from pathlib import Path

DB_PLUGIN_DIR = "nua.orchestrator.db_plugins"

LOADED_MODULES = {}
DOCKER_MODULES = set()
ASSIGN_MODULES = set()
NETWORK_MODULES = set()
FAMILY_SET = {"db": set()}


def register_db_plugins() -> list:
    for file in rso.files(DB_PLUGIN_DIR).iterdir():
        path = Path(file)
        if path.suffix != ".py":
            continue
        load_module(path.stem, DB_PLUGIN_DIR)


def load_module(name: str, plugin_dir: str):
    spec = importlib.util.find_spec(f".{name}", plugin_dir)
    if not spec:
        return
    module = spec.loader.load_module()
    if not hasattr(module, "NUA_PROPERTIES"):
        return
    LOADED_MODULES[name] = module
    classify_module(name, getattr(module, "NUA_PROPERTIES"))


def classify_module(name: str, properties: dict):
    _classify_family(name, properties)
    if properties.get("container", "") == "docker":
        DOCKER_MODULES.add(name)
    if properties.get("assign", False):
        ASSIGN_MODULES.add(name)
    if properties.get("network", False):
        NETWORK_MODULES.add(name)


def _classify_family(name: str, properties: dict):
    family = properties.get("family", "")
    target = FAMILY_SET.get(family)
    if target is not None:
        target.add(name)


def load_plugin_function(name: str, function: str) -> Callable | None:
    module = LOADED_MODULES.get("name")
    if module is None:
        return None
    if hasattr(module, function):
        return getattr(module, function)
    return None


def is_db_plugins(name: str) -> bool:
    return name in FAMILY_SET("db")


def is_docker_plugin(name: str) -> bool:
    return name in DOCKER_MODULES


def is_assignable_plugin(name: str) -> bool:
    return name in ASSIGN_MODULES


def is_network_plugin(name: str) -> bool:
    return name in NETWORK_MODULES
