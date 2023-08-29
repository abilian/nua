"""
Base class for builders.

May be refactored later into a more abstract base class.
"""
from __future__ import annotations

import abc
import logging
import tempfile
from abc import abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any

from docker.models.images import Image
from nua.lib.nua_config import NuaConfig
from nua.lib.panic import info, show, title, vfprint, vprint, warning
from nua.lib.tool.state import verbosity
from packaging.specifiers import SpecifierSet
from packaging.version import parse

from .. import config as build_config
from ..module_definitions import ModuleDefinitions

logging.basicConfig(level=logging.INFO)
CLIENT_TIMEOUT = 600


class BuilderError(Exception):
    """Builder error."""


class Builder(abc.ABC):
    """Class to hold config and other state information during build."""

    config: NuaConfig
    container_type: str
    build_dir: Path
    nua_folder: Path
    nua_base: str

    save_image: bool = True

    def __init__(self, config: NuaConfig, save_image: bool = True):
        assert isinstance(config, NuaConfig)

        self.config = config
        self.nua_base = ""
        self.build_dir = self.make_build_dir()

        self.save_image = save_image

    @abstractmethod
    def run(self):
        raise NotImplementedError()

    def post_build_notices(self):
        """Post build analysis and possible usefull information."""
        self._notice_local_volumes()

    def _notice_local_volumes(self) -> None:
        bind_volumes = [
            volume.get("source", "unknown")
            for volume in self.config.volumes
            if volume.get("type") == "directory"
        ]
        if not bind_volumes:
            return
        lines = [
            "Declaration of volume of type 'directory'.",
            "The contents of these volumes will NOT be deleted when removing the ",
            "application instance:",
        ]
        for volume in bind_volumes:
            lines.append(f"    {volume}")
        with verbosity(0):
            warning("\n".join(lines))

    def title_build(self):
        with verbosity(0):
            title(f"Building the image for {self.config.app_id}")

    def make_build_dir(self) -> Path:
        build_dir_parent = Path(
            build_config.get("build", {}).get("build_dir", "/var/tmp")  # noqa S108
        )
        if not build_dir_parent.is_dir():
            raise BuilderError(
                f"Build directory parent not found: '{build_dir_parent}'"
            )

        with verbosity(2):
            info(f"Build directory: {build_dir_parent}")

        return Path(tempfile.mkdtemp(dir=build_dir_parent))

    def merge_modules_in_config(self) -> None:
        """Merge the module detailed definition in providers.

        Modules are currently specialized images for DBs (postrgres, mariadb, ...).
        The key/values of modules can be superceded by provider statements.
        """
        for provider in self.config.providers:
            module_name = provider.get("module-name", "")
            if not module_name:
                continue
            module = ModuleDefinitions.module(module_name)
            if module is None:
                continue
            self._select_module_version(provider, module)
            self._merge_module(provider, module)

    def _select_module_version(
        self,
        provider: dict[str, Any],
        module: dict[str, Any],
    ) -> None:
        required_version = provider.get("module-version", "")
        format = module["type"]
        if format == "docker-image":
            versions = module.get("module-versions")
            if "build" not in module:
                module["build"] = {}
            if versions and required_version:
                module["build"]["base-image"] = self._higher_package_link(
                    versions, required_version
                )
            with verbosity(1):
                info("Required image:", module["build"]["base-image"])

    def _merge_module(
        self,
        provider: dict[str, Any],
        module: dict[str, Any],
    ) -> None:
        base = deepcopy(module)
        for key, value in provider.items():
            if value is None:
                continue
            if key in base:
                base_value = base[key]
                if isinstance(value, dict) and isinstance(base_value, dict):
                    base_value.update(value)
                    continue
            base[key] = value
        provider.update(base)

    def _higher_package_link(
        self,
        versions: list[dict],
        required_version: str,
        arch: str = "amd64",
    ) -> str:
        available_packages = [
            package
            for package in versions
            if package.get("version") and package.get("arch") == arch
        ]
        specifier = SpecifierSet(required_version)
        found_package: dict[str, Any] = {}
        found_version = None
        for package in available_packages:
            version = parse(package["version"])
            if version not in specifier:
                continue
            if not found_package or found_version is None or version > found_version:
                found_package = package
                found_version = version
        return found_package.get("link", "")

    def save(self, image: Image, nua_tag: str):
        dest = f"/var/tmp/{nua_tag}.tar"  # noqa S108
        chunk_size = 2**22
        step = round(image.attrs["Size"]) // 20  # pyright: ignore
        accu = 0

        with verbosity(1):
            vfprint("Saving image ")

        with open(dest, "wb") as tarfile:
            for chunk in image.save(chunk_size=chunk_size, named=True):
                tarfile.write(chunk)
                accu += len(chunk)
                if accu >= step:
                    accu -= step
                    with verbosity(1):
                        vfprint(".")

        with verbosity(1):
            vprint("")
            show("Docker image saved:")
            show(dest)
