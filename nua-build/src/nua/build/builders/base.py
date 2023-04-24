"""
Base class for builders.

May be refactored later into a more abstract base class.
"""
from __future__ import annotations

import abc
import logging
import tempfile
from abc import abstractmethod
from pathlib import Path

from docker.models.images import Image
from nua.agent.nua_config import NuaConfig
from nua.lib.panic import info, show, title, vfprint, vprint, warning
from nua.lib.tool.state import verbosity

from .. import config as build_config

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

    def __init__(self, config: NuaConfig):
        assert isinstance(config, NuaConfig)

        self.config = config
        self.nua_base = ""
        self.build_dir = self.make_build_dir()

    @abstractmethod
    def run(self):
        raise NotImplementedError()

    def post_build_notices(self):
        """Post build analysis and possible usefull information."""
        self._notice_local_volumes()

    def _notice_local_volumes(self) -> None:
        bind_volumes = [
            volume.get("source", "unknown")
            for volume in self.config.volume
            if volume.get("type") == "bind"
        ]
        if not bind_volumes:
            return
        lines = [
            "Declaration of volume of type Docker 'bind'.",
            "The contents of these volumes will NOT be deleted when removing the ",
            "application instance:",
        ]
        for volume in bind_volumes:
            lines.append(f"    {volume}")
        with verbosity(0):
            warning("\n".join(lines))

    def _title_build(self):
        title(f"Building the image for {self.config.app_id}")

    def make_build_dir(self) -> Path:
        build_dir_parent = Path(
            build_config.get("build", {}).get("build_dir", "/var/tmp")  # noqa S108
        )
        if not build_dir_parent.is_dir():
            raise BuilderError(
                f"Build directory parent not found: '{build_dir_parent}'"
            )

        with verbosity(1):
            info(f"Build directory: {build_dir_parent}")

        return Path(tempfile.mkdtemp(dir=build_dir_parent))

    def save(self, image: Image, nua_tag: str):
        dest = f"/var/tmp/{nua_tag}.tar"  # noqa S108
        chunk_size = 2**22
        step = round(image.attrs["Size"]) // 20
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
