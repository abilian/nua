"""Parse content of custom nua builders

Docker builders are defined by a json file of properties and a Dockerfile.
"""
import json
from importlib import resources as rso
from importlib.abc import Traversable
from pprint import pformat

from nua.lib.panic import vprint, vprint_magenta
from nua.lib.tool.state import verbosity

BUILDERS_DIRS: tuple[str] = ("nua.autobuild.builders",)
BUILDERS: dict[str, dict] = {}
BUILDER_NAMES: dict[str, str] = {}
initialized = False


def is_builder(name: str) -> bool:
    if not initialized:
        register_builders()
    return name in BUILDER_NAMES


def builder_info(name: str) -> dict:
    if not initialized:
        register_builders()
    return BUILDERS[BUILDER_NAMES[name]]


def builder_ids() -> list[str]:
    if not initialized:
        register_builders()
    return list(BUILDERS.keys())


def register_builders() -> None:
    global initialized
    records: dict[str, Traversable] = {}
    for dir in BUILDERS_DIRS:
        for file in rso.files(dir).iterdir():
            if not file.is_file():
                continue
            records[file.name] = file
    load_builder_configs(records)
    initialized = True
    with verbosity(3):
        _show_builders_info()


def _show_builders_info() -> None:
    vprint_magenta("builders registered:")
    vprint("BUILDERS_DIRS:", pformat(BUILDERS_DIRS))
    vprint("BUILDERS:", pformat(BUILDERS))


def load_builder_configs(records: dict[str, Traversable]) -> None:
    for name, file in records.items():
        if name.startswith("_") or not name.endswith(".json"):
            continue
        builder_config = json.loads(file.read_text(encoding="utf8"))
        if not builder_config or "app_id" not in builder_config:
            continue
        docker_file = read_docker_file(records, builder_config)
        register_builder_config(builder_config, docker_file)


def read_docker_file(records: dict[str, Traversable], builder_config: dict) -> str:
    if builder_config["container"] != "docker":
        vprint("Only Docker builders are currently supported.")
        return ""
    return records[builder_config["dockerfile"]].read_text(encoding="utf8")


def register_builder_config(builder_config: dict, docker_file: str):
    app_id = builder_config["app_id"]
    labels = builder_config["labels"]
    BUILDERS[app_id] = {
        "app_id": app_id,
        "dockerfile": docker_file,
        "labels": labels,
    }
    names = builder_config["name"]
    if isinstance(names, str):
        names = [names]
    names.append(app_id)
    for name in names:
        BUILDER_NAMES[name] = app_id
