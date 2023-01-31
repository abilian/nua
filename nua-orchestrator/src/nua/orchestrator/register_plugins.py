"""Parse content of db_plugins

Family "db" can have functions:
    - configure_db()
    - setup_db()
"""
import importlib.util
from collections.abc import Callable
from importlib import resources as rso
from pathlib import Path

LOADED_MODULES = {}
DOCKER_MODULES = set()
ASSIGN_MODULES = set()
NETWORK_MODULES = set()
FAMILIES = ("db", "something_else")
PLUGIN_DIRS = ("nua.orchestrator.db_plugins",)
FAMILY_SET = {family: set() for family in FAMILIES}


def register_plugins() -> list:
    for dir in PLUGIN_DIRS:
        if not Path(dir).is_dir():
            continue
        for file in rso.files(dir).iterdir():
            path = Path(file)
            if path.suffix != ".py":
                continue
            load_module(path.stem, dir)


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


def _is_family_plugins(name: str, family: str) -> bool:
    return name in FAMILY_SET.get(family, set())


def is_db_plugins(name: str) -> bool:
    return _is_family_plugins(name, "db")


def is_docker_plugin(name: str) -> bool:
    return name in DOCKER_MODULES


def is_assignable_plugin(name: str) -> bool:
    return name in ASSIGN_MODULES


def is_network_plugin(name: str) -> bool:
    return name in NETWORK_MODULES
