"""Parse content of db_plugins.

Family "db" can have functions:
    - configure_db()
    - setup_db()
"""
import importlib.util
from collections.abc import Callable
from importlib import resources as rso
from pathlib import Path
from pprint import pformat

from nua.agent.nua_config import hyphen_get
from nua.lib.panic import bold_debug, debug
from nua.lib.tool.state import verbosity

from .utils import dehyphen, hyphen

LOADED_MODULES = {}
MODULES_PROPERTIES = {}
DOCKER_MODULES = set()
ASSIGN_MODULES = set()
NETWORK_MODULES = set()
FAMILIES = ("db", "something_else")
PLUGIN_DIRS = ("nua.orchestrator.db_plugins",)
FAMILY_SET = {family: set() for family in FAMILIES}


def register_plugins():
    for dir in PLUGIN_DIRS:
        for file in rso.files(dir).iterdir():
            path = Path(file)
            if path.suffix != ".py" or path.stem.startswith("_"):
                continue
            load_module(path.stem, dir)
    with verbosity(3):
        _show_plugin_info()


def _show_plugin_info():
    bold_debug("plugins registered:")
    debug("PLUGIN_DIRS:", pformat(PLUGIN_DIRS))
    debug("LOADED_MODULES:", pformat(LOADED_MODULES))
    debug("DOCKER_MODULES:", pformat(DOCKER_MODULES))
    debug("ASSIGN_MODULES:", pformat(ASSIGN_MODULES))
    debug("NETWORK_MODULES:", pformat(NETWORK_MODULES))
    debug("FAMILIES:", pformat(FAMILIES))
    debug("FAMILY_SET:", pformat(FAMILY_SET))


def load_module(name: str, plugin_dir: str):
    spec = importlib.util.find_spec(f".{name}", plugin_dir)
    if not spec:
        return
    module = spec.loader.load_module()
    if not hasattr(module, "NUA_PROPERTIES"):
        return
    LOADED_MODULES[name] = module
    classify_module(name, module.NUA_PROPERTIES)


def classify_module(name: str, properties: dict):
    MODULES_PROPERTIES[name] = properties
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


def load_plugin_function(name: str, function_name: str) -> Callable | None:
    module = hyphen_get(LOADED_MODULES, name)
    if module is None:
        return None
    if hasattr(module, function_name):
        return getattr(module, function_name)
    return None


def load_plugin_meta_packages_requirement(name: str) -> list:
    "(for future use)"
    properties = hyphen_get(MODULES_PROPERTIES, "name", {})
    return properties.get("meta-packages", [])


def any_hyphen_in(some_set: set | list | dict, name: str) -> bool:
    return hyphen(name) in some_set or dehyphen(name) in some_set


def _is_family_plugins(name: str, family: str) -> bool:
    return any_hyphen_in(FAMILY_SET.get(family, set()), name)


def is_db_plugins(name: str) -> bool:
    return _is_family_plugins(name, "db")


def is_docker_plugin(name: str) -> bool:
    return any_hyphen_in(DOCKER_MODULES, name)


def is_assignable_plugin(name: str) -> bool:
    return any_hyphen_in(ASSIGN_MODULES, name)


def is_network_plugin(name: str) -> bool:
    return any_hyphen_in(NETWORK_MODULES, name)
