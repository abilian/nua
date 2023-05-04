"""Nua : search image related funcitons.
"""
from collections.abc import Generator
from operator import itemgetter
from pathlib import Path
from urllib.parse import urlparse

from nua.lib.console import print_green, print_magenta, print_red
from nua.lib.panic import vprint
from nua.lib.tool.state import verbosity
from packaging.version import Version
from packaging.version import parse as parse_version

from . import config
from .docker_utils import local_nua_images


def image_available_locally(app_name: str) -> bool:
    """Return True if image of app_name is available in local Docker daemon."""
    app, tag = parse_app_name(app_name)
    if tag:
        nua_tag = f"nua-{app}:{tag}"
        for image in local_nua_images():
            if image.labels["NUA_TAG"] == nua_tag:
                return True
    else:
        for image in local_nua_images():
            if image.labels["APP_ID"] == app:
                return True
    return False


def search_nua(app_name: str) -> list[Path]:
    """Search Nua image from the registries.

    (local registry for now).

    Return:
        list of path of local Nua archives sorted by version.
    """
    app, tag = parse_app_name(app_name)
    return search_docker_tar_local(app, tag)


def search_nua_print(app_name: str) -> list[Path]:
    """Search Nua image from the registries.

    (local registry for now).
    """
    print_magenta(f"Search image '{app_name}'")
    results = search_nua(app_name)
    if results:
        print_green(f"Search results for '{app_name}':")
        for path in results:
            print(f"    {path}")
    else:
        print_red(f"Search: no image found for '{app_name}'.")
    return results


def parse_app_name(app_name: str) -> tuple:
    demand = app_name.strip().lower()
    if demand.endswith(".tar"):
        demand = demand[:-4]
    if demand.startswith("nua-"):
        demand = demand[4:]
    splitted = demand.split(":", 1)
    app = splitted[0]
    if len(splitted) > 1:
        tag = splitted[1]
    else:
        tag = ""
    with verbosity(4):
        vprint(f"parse_app_name: {app} {tag}")
    return (app, tag)


def list_registry_docker_tar_local() -> list:
    registries = config.read("nua", "registry") or []
    return [
        reg
        for reg in sorted(registries, key=itemgetter("priority"))
        if _is_local_tar(reg)
    ]


def _is_local_tar(reg) -> bool:
    if reg["format"] != "docker_tar":
        return False
    url = urlparse(reg["url"])
    return url.scheme == "file"


def _path_tar_version(path: Path) -> Version:
    name = path.name.split(":", 1)[1]
    name = name.split(".tar")[0]
    try:
        version = parse_version(name)
    except (LookupError, TypeError, ValueError):
        version = parse_version("0")
    if not isinstance(version, Version):
        version = parse_version("0")
    return version


def search_docker_tar_local(app, tag) -> list[Path]:
    """Return list of path of local Nua archives sorted by version."""
    results: list[Path] = []
    if tag:
        for registry in list_registry_docker_tar_local():
            results.extend(path for path in find_local_tar_tagged(registry, app, tag))
    else:
        for registry in list_registry_docker_tar_local():
            results.extend(path for path in find_local_tar_untagged(registry, app))
    with verbosity(4):
        vprint(f"search_docker_tar_local list: {results}")
    version_path = sorted((_path_tar_version(p), p) for p in results)
    return [t[1] for t in version_path]


def find_local_tar_tagged(registry, app, tag) -> Generator[Path, None, None]:
    # we expect a local directory with files like 'nua-app:1.2-3.tar'
    glob_string = f"nua-{app}:{tag}.tar"
    return _find_local_tar(registry, glob_string)


def find_local_tar_untagged(registry, app) -> Generator[Path, None, None]:
    # we expect a local dirctory with files like 'nua-app:1.2-3.tar'
    glob_string = f"nua-{app}:*.tar"
    return _find_local_tar(registry, glob_string)


def _find_local_tar(registry, glob_string) -> Generator[Path, None, None]:
    folder = Path(urlparse(registry["url"]).path)
    with verbosity(4):
        vprint(f"_find_local_tar: {folder} {glob_string}")
    if folder.is_dir():
        yield from folder.rglob(glob_string)
