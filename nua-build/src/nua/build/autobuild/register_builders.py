"""Parse content of custom nua builders.

Docker builders are defined by a json file of properties and a
Dockerfile.
"""
import json
from importlib import resources as rso
from importlib.abc import Traversable
from pprint import pformat

from nua.lib.nua_config import force_list
from nua.lib.panic import bold_debug, warning, vprint
from nua.lib.tool.state import verbosity


def is_builder(name: str | dict | list) -> bool:
    register_builders()
    if isinstance(name, list):
        return all(_is_builder(x) for x in name)
    return _is_builder(name)


def _is_builder(name: str | dict) -> bool:
    if isinstance(name, str):
        return name in builder_registry.builder_names
    # for builder expressed as a dict:
    lang = name["name"]
    version = name["version"]
    return bool(builder_registry.builder_languages.get(lang, {}).get(version, None))


def builder_info(name: str | dict | list) -> dict:
    register_builders()
    if isinstance(name, list):
        # fixme: list not managed
        actual_name = name[0]
    else:
        actual_name = name
    if isinstance(actual_name, str):
        return builder_registry.builders[builder_registry.builder_names[actual_name]]
    # for builder expressed as a dict:
    lang = actual_name["name"]
    version = actual_name["version"]
    app_id = builder_registry.builder_languages.get(lang, {}).get(version, "")
    return builder_registry.builders[app_id]


def builder_ids() -> list[str]:
    register_builders()
    return list(builder_registry.builders.keys())


def register_builders() -> None:
    builder_registry.register_builders()


class BuilderRegistry:
    builders_dirs: tuple[str]
    builders: dict[str, dict]
    builder_names: dict[str, str]

    def __init__(self):
        self.is_initialized = False
        self.builders_dirs = ("nua.build.autobuild.builders",)
        self.builders = {}
        self.builder_names = {}
        self.builder_languages = {}

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
        for dir in self.builders_dirs:
            for file in rso.files(dir).iterdir():
                if not file.is_file():
                    continue
                records[file.name] = file
        return records

    def show_builders_info(self) -> None:
        bold_debug("Builders registered:")
        vprint("BUILDERS_DIRS:", pformat(self.builders_dirs))
        vprint("BUILDERS:", pformat(self.builders))

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
            warning("Only Docker builders are currently supported.")
            return ""
        return records[builder_config["dockerfile"]].read_text(encoding="utf8")

    def register_builder_config(self, builder_config: dict, docker_file: str):
        app_id = builder_config["app_id"]
        labels = builder_config["labels"]
        self.builders[app_id] = {
            "app_id": app_id,
            "dockerfile": docker_file,
            "labels": labels,
            "container": builder_config.get("container", ""),
            "language_name": builder_config.get("language_name", ""),
            "language_version": builder_config.get("language_version", ""),
        }
        names = force_list(builder_config["name"])
        names.append(app_id)
        for name in names:
            self.builder_names[name] = app_id
        language_names = force_list(builder_config.get("language_name", []))
        language_version = builder_config.get("language_version", "1.0")
        for lang_name in language_names:
            versions = self.builder_languages.setdefault(lang_name, {})
            versions[language_version] = app_id


builder_registry = BuilderRegistry()
