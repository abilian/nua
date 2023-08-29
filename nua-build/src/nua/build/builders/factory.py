"""Builder factory: create a Builder instance based on the nua-config.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from pprint import pformat
from typing import Any

from nua.lib.nua_config import NuaConfig
from nua.lib.panic import info, vprint
from nua.lib.tool.state import verbosity

from .base import Builder, BuilderError
from .docker import DockerBuilder
from .wrap import DockerWrapBuilder


def get_builder(config_or_path: NuaConfig | str | Path = "", **opts) -> Builder:
    if isinstance(config_or_path, NuaConfig):
        config = config_or_path
    else:
        config = NuaConfig(config_or_path)
    factory = BuilderFactory(config, opts)
    return factory.get_builder()


@dataclass(frozen=True)
class BuilderFactory:
    """Factory to create a Builder instance."""

    config: NuaConfig
    opts: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert isinstance(self.config, NuaConfig)

    def get_builder(self) -> Builder:
        with verbosity(4):
            vprint(pformat(self.config.as_dict()))

        # Not used at this stage
        # container_type = self.detect_container_type()
        # if self.opts.get("provider"):
        #     # build_method = self.detect_build_method()
        #     return DockerBuilder(self.config, **self.opts)

        build_method = self.detect_build_method()

        if build_method == "build":
            return DockerBuilder(self.config, **self.opts)

        if build_method == "wrap":
            return DockerWrapBuilder(self.config, **self.opts)

        raise ValueError(f"Unknown build strategy '{build_method}'")

    # XXX: not used
    def detect_container_type(self) -> str:
        """Placeholder for future container technology detection.

        Currently only Docker is supported.
        """
        container = self.config.build.get("container") or "docker"
        if container != "docker":
            raise BuilderError(f"Unknown container type: '{container}'")
        return container

    def detect_build_method(self) -> str:
        """Detect how to build the container.

        For now 2 choices:
        - build: full build from generated Dockerfile
        - wrap: use existing Docker image and add Nua metadata
        """
        method = self.config.build_method or self.build_method_from_data()
        if method not in {"build", "wrap"}:
            raise BuilderError(f"Unknown build method: '{method}'")
        with verbosity(3):
            info(f"Build method: {method}")
        return method

    def build_method_from_data(self) -> str:
        if self.config.wrap_image:
            with verbosity(3):
                info(f"metadata.wrap_image: {self.config.wrap_image}")
            return "wrap"
        return "build"
