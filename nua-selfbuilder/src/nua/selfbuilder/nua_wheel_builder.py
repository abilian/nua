"""Script to build Nua own images.
"""
import re
import tempfile
from os import chdir
from pathlib import Path
from shutil import copy2
from typing import Optional

import docker
from docker import DockerClient, from_env
from docker.errors import APIError, BuildError, ImageNotFound, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from nua.lib.common.panic import error
from nua.lib.common.rich_console import print_green
from nua.lib.common.shell import mkdir_p, rm_fr, sh
from nua.lib.tool.state import verbosity

from ..constants import (
    DOCKERFILE_BUILDER,
    DOCKERFILE_PYTHON,
    NUA_BUILDER_TAG,
    NUA_LINUX_BASE,
    NUA_PYTHON_TAG,
    NUA_WHEEL_DIR,
)
from . import __version__
from .docker_utils_build import display_docker_img, docker_build_log_error


class NuaWheelBuilder:
    def __init__(self):
        self.orig_wd = None
        self.wheels_path = []

    def make_wheels(self) -> bool:
        self.orig_wd = Path.cwd()
        if self.check_devel_mode():
            done = self.build_from_local()
        else:
            done = self.build_from_download()
        chdir(self.orig_wd)
        return done

    def wheels(self) -> list:
        return self.wheels_path

    @staticmethod
    def _nua_top(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent.parent

    def check_devel_mode(self) -> bool:
        """Try to find all required files locally in an up to date git."""
        try:
            nua_top = self._nua_top()
            return all(
                (nua_top / ".git").is_dir(),
                (nua_top / "nua-lib" / "pyproject.toml").is_file(),
                (nua_top / "nua-runtime" / "pyproject.toml").is_file(),
            )
        except (ValueError, OSError):
            return False

    def build_from_local(self):
        return self.build_from(self._nua_top())

    def build_from_download(self):
        pass

    def build_from(self, top_git: Path) -> bool:
        return all(self.build_nua_lib(top_git), self.build_nua_runtime(top_git))

    def build_nua_lib(self, top_git: Path) -> bool:
        return self.poetry_build(top_git / "nua-lib")

    def build_nua_runtime(self, top_git: Path) -> bool:
        return self.poetry_build(top_git / "nua-runtime")

    def poetry_build(self, path: Path) -> bool:
        chdir(path)
        rm_fr(path / "dist")
        cmd = "poetry build -f wheel"
        result = sh(cmd, capture_output=True)
        if not (done := re.search("- Built(.*)\n", result)):
            return False
        built = done.group(1).strip()  # type: ignore
        self.wheels_path.append(path / "dist" / built)
        return True
