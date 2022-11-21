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

from ..constants import (
    DOCKERFILE_BUILDER,
    DOCKERFILE_PYTHON,
    NUA_BUILDER_TAG,
    NUA_LINUX_BASE,
    NUA_PYTHON_TAG,
    NUA_WHEEL_DIR,
)
from . import __version__ as nua_version
from .docker_utils_build import display_docker_img, docker_build_log_error
from .nua_wheel_builder import NuaWheelBuilder


class NUAImageBuilder:
    def __init__(self):
        self.orig_wd = None
        self.images_path = {}

    def run(self, force: bool = True) -> dict:
        self.orig_wd = Path.cwd()
        self.ensure_nua_python(force)
        self.ensure_nua_builder(force)
        chdir(self.orig_wd)
        return self.images_path

    def ensure_nua_python(self, force: bool):
        if not docker_require(NUA_PYTHON_TAG, force):
            self.build_nua_python()
        if verbosity(1):
            display_docker_img(NUA_PYTHON_TAG)

    def ensure_nua_builder(self, force: bool):
        if not docker_require(NUA_BUILDER_TAG, force):
            self.build_nua_builder()
        if verbosity(1):
            display_docker_img(NUA_BUILDER_TAG)

    def build_nua_python(self):
        print_green(f"Build of the docker image {NUA_PYTHON_TAG}")
        with tempfile.TemporaryDirectory() as build_dir:
            copy2(DOCKERFILE_PYTHON, build_dir)
            if verbosity(3):
                print(f"build directory: {build_dir}")
            chdir(build_dir)
            self.docker_build_python()

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
            rm=False,
        )

    def build_nua_builder(self):
        print_green(f"Build of the docker image {NUA_BUILDER_TAG}")
        with tempfile.TemporaryDirectory() as build_dir:
            copy2(DOCKERFILE_BUILDER, build_dir)
            self.copy_wheels(build_dir)
            if verbosity(3):
                print(f"build directory: {build_dir}")
            chdir(build_dir)
            self.docker_build_builder()

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
            rm=False,
        )

    def copy_wheels(self, build_dir: Path):
        wheel_builder = NuaWheelBuilder()
        wheel_builder.make_wheels()
        destination = build_dir / "nua_build_whl"
        mkdir_p(destination)
        for wheel in wheel_builder.wheels():
            copy2(wheel, destination)


def docker_require(reference: str, force: bool) -> Image | None:
    if force:
        return None
    else:
        return docker_get_locally(reference) or docker_pull(reference)


def docker_get_locally(reference: str) -> Image | None:
    client = from_env()
    try:
        return client.images.pull(reference)
    except (APIError, ImageNotFound):
        return None


def docker_pull(reference: str) -> Image | None:
    client = from_env()
    try:
        return client.images.pull(reference)
    except (APIError, ImageNotFound):
        return None
