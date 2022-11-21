"""Script to build Nua own images.
"""
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
from nua.lib.common.shell import mkdir_p, rm_fr
from nua.lib.tool.state import verbosity

from . import __version__ as nua_version
from .constants import (
    DOCKERFILE_BUILDER,
    DOCKERFILE_PYTHON,
    NUA_BUILDER_TAG,
    NUA_LINUX_BASE,
    NUA_PYTHON_TAG,
    NUA_WHEEL_DIR,
)
from .docker_build_utils import (
    display_docker_img,
    docker_build_log_error,
    docker_remove_locally,
    docker_require,
)
from .nua_wheel_builder import NuaWheelBuilder


class NUAImageBuilder:
    def __init__(self):
        self.orig_wd = None
        self.images_path = {}
        self.force = False
        self.download = False

    def build(self, force: bool = False, download: bool = False) -> dict:
        self.force = force
        self.download = download
        if verbosity(2):
            if self.force:
                print("Force rebuild of images")
            if self.download:
                print("Force download of source code")
        self.orig_wd = Path.cwd()
        self.ensure_nua_python()
        self.ensure_nua_builder()
        chdir(self.orig_wd)
        return self.images_path

    def ensure_nua_python(self):
        if self.force or not docker_require(NUA_PYTHON_TAG):
            if self.force:
                docker_remove_locally(NUA_PYTHON_TAG)
            self.build_nua_python()
        if verbosity(1):
            display_docker_img(NUA_PYTHON_TAG)

    def ensure_nua_builder(self):
        if self.force or not docker_require(NUA_BUILDER_TAG):
            if self.force:
                docker_remove_locally(NUA_BUILDER_TAG)
            self.build_nua_builder()
        if verbosity(1):
            display_docker_img(NUA_BUILDER_TAG)

    def build_nua_python(self):
        print_green(f"Build of the docker image {NUA_PYTHON_TAG}")
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            if verbosity(3):
                print(f"build directory: {build_path}")
            copy2(DOCKERFILE_PYTHON, build_path)
            chdir(build_path)
            docker_build_python()

    def build_nua_builder(self):
        print_green(f"Build of the docker image {NUA_BUILDER_TAG}")
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            if verbosity(3):
                print(f"build directory: {build_path}")
            copy2(DOCKERFILE_BUILDER, build_path)
            self.copy_wheels(build_path)
            chdir(build_path)
            docker_build_builder()

    def copy_wheels(self, build_path: Path):
        wheel_path = build_path / "nua_build_whl"
        mkdir_p(wheel_path)
        wheel_builder = NuaWheelBuilder(wheel_path, self.download)
        success = wheel_builder.make_wheels()


@docker_build_log_error
def docker_build_python():
    app_id = "nua-python"
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_PYTHON).name,
        buildargs={"nua_linux_base": NUA_LINUX_BASE},
        tag=NUA_PYTHON_TAG,
        labels={
            "APP_ID": app_id,
            "NUA_TAG": NUA_PYTHON_TAG,
            "NUA_BUILD_VERSION": nua_version,
        },
        rm=True,
    )


@docker_build_log_error
def docker_build_builder():
    app_id = "nua-builder"
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_BUILDER).name,
        buildargs={"nua_python_tag": NUA_PYTHON_TAG, "nua_version": nua_version},
        tag=NUA_BUILDER_TAG,
        labels={
            "APP_ID": app_id,
            "NUA_TAG": NUA_BUILDER_TAG,
            "NUA_BUILD_VERSION": nua_version,
        },
        rm=True,
    )
