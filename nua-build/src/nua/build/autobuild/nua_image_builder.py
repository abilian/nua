"""Script to build Nua own images."""
import tempfile
from pathlib import Path
from pprint import pformat
from nua.lib.actions import copy_from_package
from nua.lib.backports import chdir
from nua.lib.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG
from nua.lib.docker import (
    display_docker_img,
    docker_remove_locally,
    docker_require,
    docker_stream_build,
)
from nua.lib.nua_config import force_list
from nua.lib.panic import Abort, show, title, debug, vprint
from nua.lib.shell import mkdir_p
from nua.lib.tool.state import verbosity

from .. import __version__ as nua_version
from .constants import DOCKERFILE_BUILDER, DOCKERFILE_PYTHON, NUA_LINUX_BASE
from .nua_wheel_builder import NuaWheelBuilder
from .register_builders import builder_ids, builder_info, is_builder


class NuaImageBuilder:
    def __init__(self):
        self.orig_wd = None
        self.images_path = {}
        self.force = False
        self.download = False
        self.displayed = set()

    def build(
        self, force: bool = False, download: bool = False, all: bool = True
    ) -> dict:
        self.force = force
        self.download = download
        with verbosity(2):
            if self.force:
                show("Force rebuild of images")
            if self.download:
                show("Force download of source code")

        self.ensure_nua_python()
        self.ensure_nua_builder()
        if all:
            # build all base images
            self.ensure_all_nua_builders()

        return self.images_path

    def ensure_nua_python(self):
        if self.force or not docker_require(NUA_PYTHON_TAG):
            if self.force:
                docker_remove_locally(NUA_PYTHON_TAG)
            self.build_nua_python()

        with verbosity(1):
            self.display_once_docker_img(NUA_PYTHON_TAG)

    def ensure_nua_builder(self):
        if self.force or not docker_require(NUA_BUILDER_TAG):
            if self.force:
                docker_remove_locally(NUA_BUILDER_TAG)
            self.build_nua_builder()

        with verbosity(1):
            self.display_once_docker_img(NUA_BUILDER_TAG)

    def ensure_all_nua_builders(self):
        """Build the (several) build images providing various environments."""
        for app_id in builder_ids():
            self.ensure_nua_builder_custom(app_id)

    def ensure_nua_builder_custom(self, name: str | dict):
        info = builder_info(name)
        with verbosity(3):
            debug("ensure_nua_builder_custom:", pformat(info))
        if info.get("container", "") != "docker":
            return
        app_id = info["app_id"]
        tag = self.builder_tag(name)
        if self.force or not docker_require(tag):
            if self.force:
                docker_remove_locally(tag)
            self.build_builder_of_name(app_id)

        with verbosity(1):
            self.display_once_docker_img(tag)

    def display_once_docker_img(self, image_tag: str):
        if image_tag not in self.displayed:
            display_docker_img(image_tag)
            self.displayed.add(image_tag)

    def ensure_images(self, required: list | str | dict):
        with verbosity(3):
            debug("ensure_images:", required)

        self.ensure_base_image()

        if not required:
            with verbosity(3):
                vprint("no image required")
            return

        required = force_list(required)
        for key in required:
            if not is_builder(key):
                raise Abort(f"'{key}' is not a known Nua builder.")
        for key in required:
            self.ensure_nua_builder_custom(key)

    def ensure_base_image(self):
        with verbosity(3):
            debug("ensure_base_image()")
        self.build(force=False, all=False)

    def build_nua_python(self):
        with verbosity(0):
            title(f"Building the docker image {NUA_PYTHON_TAG}")
        info = {
            "app_id": "nua-python",
            "tag": NUA_PYTHON_TAG,
            "labels": {},
            "buildargs": {
                "nua_linux_base": NUA_LINUX_BASE,
            },
        }
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            with verbosity(3):
                show(f"build directory: {build_path}")
            copy_from_package(
                "nua.build.autobuild.dockerfiles",
                DOCKERFILE_PYTHON,
                build_path,
                "Dockerfile",
            )
            docker_build_custom(info, build_path)

    def build_nua_builder(self):
        with verbosity(0):
            title(f"Building the docker image {NUA_BUILDER_TAG}")
        info = {
            "app_id": "nua-builder",
            "tag": NUA_BUILDER_TAG,
            "labels": {},
            "buildargs": {
                "nua_python_tag": NUA_PYTHON_TAG,
                "nua_version": nua_version,
            },
        }
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            with verbosity(3):
                show(f"build directory: {build_path}")
            copy_from_package(
                "nua.build.autobuild.dockerfiles",
                DOCKERFILE_BUILDER,
                build_path,
                "Dockerfile",
            )
            self.copy_wheels(build_path)
            docker_build_custom(info, build_path)

    def build_builder_of_name(self, name: str | dict | list):
        """Build a specific environmanet builder."""
        info = builder_info(name)
        tag = self.builder_tag(name)
        info["tag"] = tag
        info["buildargs"] = {
            "nua_builder_tag": NUA_BUILDER_TAG,
            "nua_version": nua_version,
        }
        with verbosity(0):
            title(f"Building the docker image {tag}")
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            with verbosity(3):
                show(f"build directory: {build_path}")
            dockerfile_path = build_path / "Dockerfile"
            dockerfile_path.write_text(info["dockerfile"])
            docker_build_custom(info, build_path)

    @staticmethod
    def builder_tag(name: str | dict | list) -> str:
        info = builder_info(name)
        app_id = info["app_id"]
        return f"{app_id}:{nua_version}"

    def copy_wheels(self, build_path: Path):
        wheel_path = build_path / "nua_build_whl"
        mkdir_p(wheel_path)
        wheel_builder = NuaWheelBuilder(wheel_path, self.download)
        if not wheel_builder.make_wheels():
            raise Abort("Build of required Nua wheels failed")


def docker_build_custom(info: dict, build_path: Path):
    with chdir(build_path):
        tag = info["tag"]
        labels = {
            "APP_ID": info["app_id"],
            "NUA_TAG": tag,
            "NUA_BUILD_VERSION": nua_version,
        }
        labels.update(info["labels"])
        buildargs = info["buildargs"]
        docker_stream_build(".", tag, buildargs, labels)
