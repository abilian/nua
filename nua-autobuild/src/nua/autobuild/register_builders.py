"""Parse content of custom nua builders

Docker builders are defined by a json file of properties and a Dockerfile.
"""
import json
from importlib import resources as rso
from pathlib import Path
from pprint import pformat

from nua.lib.panic import vprint, vprint_magenta
from nua.lib.tool.state import verbosity

BUILDERS_DIRS = ("nua.autobuild.builders",)
BUILDERS = {}
BUILDER_NAMES = {}
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
    return list(BUILDERS.key())


def register_builders() -> None:
    global initialized
    for dir in BUILDERS_DIRS:
        for file in rso.files(dir).iterdir():
            path = Path(file)
            if path.suffix != ".json" or path.stem.startswith("_"):
                continue
            load_builder_config(path, dir)
    initialized = True
    with verbosity(3):
        _show_builders_info()


def _show_builders_info() -> None:
    vprint_magenta("builders registered:")
    vprint("BUILDERS_DIRS:", pformat(BUILDERS_DIRS))
    vprint("BUILDERS:", pformat(BUILDERS))


def load_builder_config(path: Path, builder_dir: str) -> None:
    builder_config = json.loads(path.read_text(encoding="utf8"))
    if not builder_config or "app_id" not in builder_config:
        return
    classify_builder(builder_config, builder_dir)


def classify_builder(builder_config: dict, builder_dir) -> None:
    if builder_config["container"] != "docker":
        vprint("Only Docker builders are currently supported.")
        return
    docker_file = Path(builder_dir) / builder_config["dockerfile"]
    if not docker_file.is_file():
        vprint("Missing Dockerfile {docker_file}")
        return
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
