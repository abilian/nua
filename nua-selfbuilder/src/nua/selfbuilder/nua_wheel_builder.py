"""Script to build Nua own images.
"""
import re
import tempfile
import zipfile
from os import chdir
from pathlib import Path
from shutil import copy2
from typing import Optional
from urllib.request import urlopen

import docker
from docker import DockerClient, from_env
from docker.errors import APIError, BuildError, ImageNotFound, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from nua.lib.common.panic import error
from nua.lib.common.rich_console import print_green
from nua.lib.common.shell import mkdir_p, rm_fr, sh
from nua.lib.tool.state import verbosity

from . import __version__
from .constants import (
    CODE_URL,
    DOCKERFILE_BUILDER,
    DOCKERFILE_PYTHON,
    NUA_BUILDER_TAG,
    NUA_LINUX_BASE,
    NUA_PYTHON_TAG,
    NUA_WHEEL_DIR,
)
from .docker_build_utils import display_docker_img, docker_build_log_error


class NuaWheelBuilder:
    def __init__(self, wheel_path: Path, download: bool = False):
        self.wheel_path = wheel_path
        self.build_path = None
        self.download = download

    def make_wheels(self) -> bool:
        if not self.download and self.check_devel_mode():
            if verbosity(3):
                print("make_wheels(): local git found")
            done = self.build_from_local()
        else:
            if verbosity(3):
                if self.download:
                    print("make_wheels(): download of source code forced")
                else:
                    print("make_wheels(): local git not found, will download")
            done = self.build_from_download()
        return done

    @staticmethod
    def _nua_top() -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent.parent

    def check_devel_mode(self) -> bool:
        """Try to find all required files locally in an up to date git."""
        try:
            nua_top = self._nua_top()
            return all(
                (
                    (nua_top / ".git").is_dir(),
                    (nua_top / "nua-lib" / "pyproject.toml").is_file(),
                    (nua_top / "nua-runtime" / "pyproject.toml").is_file(),
                )
            )
        except (ValueError, OSError):
            return False

    def build_from_local(self):
        return self.build_from(self._nua_top())

    def build_from_download(self):
        with tempfile.TemporaryDirectory() as build_dir:
            self.build_path = Path(build_dir)
            if verbosity(3):
                print(f"build_from_download() directory: {self.build_path}")
            target = self.build_path / "nua.zip"
            if verbosity(3):
                print(f"Dowloading '{CODE_URL}'")
            with urlopen(CODE_URL) as remote:
                target.write_bytes(remote.read())
            with zipfile.ZipFile(target, "r") as zfile:
                zfile.extractall(self.build_path)
            self.build_from(self.build_path / "nua-main")

    def build_from(self, top_git: Path) -> bool:
        if not (top_git.is_dir()):
            error(f"Directory not found '{top_git}'")
        if verbosity(3):
            print(list(f.name for f in top_git.iterdir()))
        return all((self.build_nua_lib(top_git), self.build_nua_runtime(top_git)))

    def build_nua_lib(self, top_git: Path) -> bool:
        return self.poetry_build(top_git / "nua-lib")

    def build_nua_runtime(self, top_git: Path) -> bool:
        return self.poetry_build(top_git / "nua-runtime")

    def poetry_build(self, path: Path) -> bool:
        if verbosity(3):
            print(f"Poetry build in '{path}'")
        chdir(path)
        rm_fr(path / "dist")
        cmd = "poetry build -f wheel"
        result = sh(cmd, capture_output=True, show_cmd=False)
        if not (done := re.search("- Built(.*)\n", result)):
            warning(f"Wheel not found for '{path}'")
            return False
        built = done.group(1).strip()  # type: ignore
        wheel = path / "dist" / built
        copy2(wheel, self.wheel_path)
        if verbosity(2):
            print(f"Wheel copied: '{built}'")
        return True
