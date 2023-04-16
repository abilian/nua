"""Parse content of custom nua builders.

Docker builders are defined by a json file of properties and a
Dockerfile.
"""
import json
from importlib import resources as rso
from importlib.abc import Traversable
from pprint import pformat

from nua.lib.panic import vprint, vprint_magenta
from nua.lib.tool.state import verbosity


def is_builder(name: str) -> bool:
    register_builders()
    return name in builder_registry.BUILDER_NAMES


def builder_info(name: str) -> dict:
    register_builders()
    return builder_registry.BUILDERS[builder_registry.BUILDER_NAMES[name]]


def builder_ids() -> list[str]:
    register_builders()
    return list(builder_registry.BUILDERS.keys())


def register_builders() -> None:
    builder_registry.register_builders()


class BuilderRegistry:
    BUILDERS_DIRS: tuple[str]
    BUILDERS: dict[str, dict]
    BUILDER_NAMES: dict[str, str]

    def __init__(self):
        self.is_initialized = False
        self.BUILDERS_DIRS = ("nua.autobuild.builders",)
        self.BUILDERS = {}
        self.BUILDER_NAMES = {}

    def register_builders(self) -> None:
        if self.is_initialized:
            return

        records = self.get_records()
        self.load_builder_configs(records)
        self.is_initialized = True
        with verbosity(3):
            self.show_builders_info()

    def get_records(self):
        records: dict[str, Traversable] = {}
        for dir in self.BUILDERS_DIRS:
            for file in rso.files(dir).iterdir():
                if not file.is_file():
                    continue
                records[file.name] = file
        return records

    def show_builders_info(self) -> None:
        vprint_magenta("Builders registered:")
        vprint("BUILDERS_DIRS:", pformat(self.BUILDERS_DIRS))
        vprint("BUILDERS:", pformat(self.BUILDERS))

    def load_builder_configs(self, records: dict[str, Traversable]) -> None:
        for name, file in records.items():
            if name.startswith("_") or not name.endswith(".json"):
                continue
            builder_config = json.loads(file.read_text(encoding="utf8"))
            if not builder_config or "app_id" not in builder_config:
                continue
            docker_file = self.read_docker_file(records, builder_config)
            self.register_builder_config(builder_config, docker_file)

    def read_docker_file(
        self, records: dict[str, Traversable], builder_config: dict
    ) -> str:
        if builder_config["container"] != "docker":
            vprint("Only Docker builders are currently supported.")
            return ""
        return records[builder_config["dockerfile"]].read_text(encoding="utf8")

    def register_builder_config(self, builder_config: dict, docker_file: str):
        app_id = builder_config["app_id"]
        labels = builder_config["labels"]
        self.BUILDERS[app_id] = {
            "app_id": app_id,
            "dockerfile": docker_file,
            "labels": labels,
        }
        names = builder_config["name"]
        if isinstance(names, str):
            names = [names]
        names.append(app_id)
        for name in names:
            self.BUILDER_NAMES[name] = app_id


builder_registry = BuilderRegistry()
