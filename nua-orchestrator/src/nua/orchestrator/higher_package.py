"""Provide a resource matching a version requirement.

Parse the content of `nua.orchestrator` plugins dir for .json files to
find the relevant package/version.
"""
import json
from functools import cache
from importlib import resources as rso
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import parse

from .register_plugins import PLUGIN_DIRS


@cache
def package_list(package_name: str, arch: str) -> list:
    packages = []
    for dir in PLUGIN_DIRS:
        for file in rso.files(dir).iterdir():
            path = Path(file)
            if path.suffix != ".json":
                continue
            packages.extend(load_packages(package_name, arch, path))
    return packages


def load_packages(name: str, arch: str, path: Path) -> list:
    content = json.loads(path.read_text(encoding="utf8"))
    return [package for package in content.get(name, []) if package["arch"] == arch]


def higher_package(
    package_name: str, required_version: str, arch: str = "amd64"
) -> dict:
    specifier = SpecifierSet(required_version)
    found_package = {}
    found_version = None
    for package in package_list(package_name, arch):
        version = parse(package["version"])
        if version not in specifier:
            continue
        if not found_package or version > found_version:
            found_package = package
            found_version = version
    return found_package
