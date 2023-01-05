"""Script to build Nua own images."""
import tempfile
from os import chdir
from pathlib import Path

import docker
from nua.lib.actions import copy_from_package
from nua.lib.panic import abort, show, title
from nua.lib.shell import mkdir_p
from nua.lib.tool.state import verbosity
from nua.runtime.constants import (
    NUA_BUILDER_NODE_TAG16,
    NUA_BUILDER_TAG,
    NUA_PYTHON_TAG,
)

from . import __version__ as nua_version
from .constants import (
    DOCKERFILE_BUILDER,
    DOCKERFILE_BUILDER_NODE16,
    DOCKERFILE_PYTHON,
    NUA_LINUX_BASE,
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

    def build(
        self, force: bool = False, download: bool = False, all: bool = True
    ) -> dict:
        self.force = force
        self.download = download
        if verbosity(2):
            if self.force:
                show("Force rebuild of images")
            if self.download:
                show("Force download of source code")
        self.orig_wd = Path.cwd()
        self.ensure_nua_python()
        self.ensure_nua_builder()
        if all:
            self.ensure_nua_builder_node()
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

    def ensure_nua_builder_node(self):
        if self.force or not docker_require(NUA_BUILDER_NODE_TAG16):
            if self.force:
                docker_remove_locally(NUA_BUILDER_NODE_TAG16)
            self.build_nua_builder_node()
        if verbosity(1):
            display_docker_img(NUA_BUILDER_NODE_TAG16)

    def build_nua_python(self):
        title(f"Building the docker image {NUA_PYTHON_TAG}")
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            if verbosity(3):
                show(f"build directory: {build_path}")
            copy_from_package(
                "nua.autobuild.dockerfiles", DOCKERFILE_PYTHON, build_path
            )
            chdir(build_path)
            docker_build_python()

    def build_nua_builder(self):
        title(f"Building the docker image {NUA_BUILDER_TAG}")
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            if verbosity(3):
                show(f"build directory: {build_path}")
            copy_from_package(
                "nua.autobuild.dockerfiles", DOCKERFILE_BUILDER, build_path
            )
            self.copy_wheels(build_path)
            chdir(build_path)
            docker_build_builder()

    def build_nua_builder_node(self):
        title(f"Building the docker image {NUA_BUILDER_NODE_TAG16}")
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            if verbosity(3):
                show(f"build directory: {build_path}")
            # Fixme: later do a dedicated dockerfile for nodejs, now using base image
            copy_from_package(
                "nua.autobuild.dockerfiles", DOCKERFILE_BUILDER_NODE16, build_path
            )
            self.copy_wheels(build_path)
            chdir(build_path)
            docker_build_builder_node()

    def copy_wheels(self, build_path: Path):
        wheel_path = build_path / "nua_build_whl"
        mkdir_p(wheel_path)
        wheel_builder = NuaWheelBuilder(wheel_path, self.download)
        if not wheel_builder.make_wheels():
            abort("Build of required Nua wheels failed")


@docker_build_log_error
def docker_build_python():
    app_id = "nua-python"
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=DOCKERFILE_PYTHON,
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
        dockerfile=DOCKERFILE_BUILDER,
        buildargs={"nua_python_tag": NUA_PYTHON_TAG, "nua_version": nua_version},
        tag=NUA_BUILDER_TAG,
        labels={
            "APP_ID": app_id,
            "NUA_TAG": NUA_BUILDER_TAG,
            "NUA_BUILD_VERSION": nua_version,
        },
        rm=True,
    )


@docker_build_log_error
def docker_build_builder_node():
    app_id = "nua-builder-nodejs16"
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=DOCKERFILE_BUILDER_NODE16,
        buildargs={"nua_builder_tag": NUA_BUILDER_TAG, "nua_version": nua_version},
        tag=NUA_BUILDER_NODE_TAG16,
        labels={
            "APP_ID": app_id,
            "NUA_TAG": NUA_BUILDER_TAG,
            "NUA_BUILD_VERSION": nua_version,
        },
        rm=True,
    )
