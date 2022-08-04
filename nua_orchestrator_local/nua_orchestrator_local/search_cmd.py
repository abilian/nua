"""Nua : search image related funcitons.
"""
from operator import itemgetter
from pathlib import Path
from urllib.parse import urlparse

from . import config
from .rich_console import print_green, print_magenta, print_red


def search_nua(app_name: str):
    """Search Nua image from the registries. (local registry for now)."""
    print_magenta(f"Search image '{app_name}'")
    app, tag = parse_app_name(app_name)
    results = search_docker_tar_local(app, tag)
    if results:
        print_green(f"Search results for '{app_name}':")
        for path in results:
            print(f"    {path}")
    else:
        print_red(f"No image found for '{app_name}'.")


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
    return (app, tag)


def list_registry_docker_tar_local() -> list:
    registries = config.read("nua", "registry")
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


def search_docker_tar_local(app, tag) -> list:
    results = []
    if tag:
        for registry in list_registry_docker_tar_local():
            results.extend(path for path in find_local_tar_tagged(registry, app, tag))
    else:
        for registry in list_registry_docker_tar_local():
            results.extend(path for path in find_local_tar_untagged(registry, app))
    return results


def find_local_tar_tagged(registry, app, tag) -> Path:
    # we expect a local dirctory with files like 'nua-app:1.2-3.tar'
    folder = Path(urlparse(registry["url"]).path)
    if folder.is_dir():
        yield from folder.rglob(f"nua-{app}:{tag}.tar")


def find_local_tar_untagged(registry, app) -> Path:
    # we expect a local dirctory with files like 'nua-app:1.2-3.tar'
    folder = Path(urlparse(registry["url"]).path)
    if folder.is_dir():
        yield from folder.rglob(f"nua-{app}:*.tar")
