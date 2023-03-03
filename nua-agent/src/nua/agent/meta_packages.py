"""Parse the meta-packages requirements."""
import json
from functools import cache
from importlib import resources as rso

DEPS_DIR = "nua.agent.deps"
META_PACKAGES_FILE = "meta_packages.json"


@cache
def _parse_meta_packages() -> dict:
    resource_path = rso.files(DEPS_DIR).joinpath(META_PACKAGES_FILE)
    return json.loads(resource_path.read_text(encoding="utf8"))


def meta_packages_requirements(name: str) -> list:
    all_deps = _parse_meta_packages()
    return all_deps.get(name, [])
