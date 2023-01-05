"""Builder class, core of build process.

Builder instance maintains config and other state information during build.

Typical use:
    builder = Builder(config_file)
    builder.run()
"""
import logging
import re
import tempfile
from contextlib import suppress
from importlib import resources as rso
from os import chdir
from pathlib import Path
from shutil import copy2, copytree

import docker
from docker.errors import BuildError
from docker.utils.json_stream import json_stream
from nua.autobuild.docker_build_utils import (
    display_docker_img,
    docker_build_log_error,
    image_labels,
    print_log_stream,
)
from nua.autobuild.nua_image_builder import NUAImageBuilder
from nua.lib.console import print_stream_blue
from nua.lib.panic import abort, info, show, title
from nua.lib.shell import rm_fr
from nua.lib.tool.state import verbosity
from nua.runtime.constants import NUA_BUILDER_NODE_TAG14, NUA_BUILDER_NODE_TAG16, NUA_BUILDER_TAG
from nua.runtime.nua_config import NuaConfig
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import __version__, config
from .constants import NUA_CONFIG

logging.basicConfig(level=logging.INFO)

RE_SUCCESS = re.compile(r"(^Successfully built |sha256:)([0-9a-f]+)$")
# beyond base image NUA_BUILDER_TAG, permit other build base. Currently tested with
# a Nodejs16 base image:
ALLOWED_PROFILE = {"node": [NUA_BUILDER_NODE_TAG14, NUA_BUILDER_NODE_TAG16]}


class Builder:
    """Class to hold config and other state information during build."""

    container_type = ""
    build_dir: Path
    nua_dir: Path
    nua_dir_relative: Path

    def __init__(self, config_file):
        self.config = NuaConfig(config_file)
        self.nua_base = ""

    def run(self):
        self.detect_container_type()
        self.check_allowed_base_image()
        self.ensure_base_image_profile_availability()
        self.select_base_image()
        title(f"Building the image for {self.config.app_id}")
        self.detect_nua_dir()
        self.nua_dir_relative = self.nua_dir.relative_to(self.config.root_dir)
        if self.container_type == "docker":
            self.build_docker_image()

    def detect_container_type(self):
        """Placeholder for future container technology detection.

        Currently only Docker is supported.
        """
        container = self.config.build.get("container") or "docker"
        if container != "docker":
            abort(f"Unknown container type: '{container}'")
        self.container_type = container

    def check_allowed_base_image(self):
        for key in self.config.profile:
            if key not in ALLOWED_PROFILE:
                abort(
                    f"Nua profile must be one of:\n{', '.join(ALLOWED_PROFILE.keys())}"
                )

    # def ensure_base_image_availability(self):
    #     if docker_get_locally(self.config.nua_base):
    #         return
    #     info(
    #         f"Required Nua base image '{self.config.nua_base}' not found, "
    #         "image build required."
    #     )
    #     image_builder = NUAImageBuilder()
    #     image_builder.build(all=True)

    def ensure_base_image_profile_availability(self):
        """Profile will determine the required base image.

        If empty, the standard Nua base image is used.
        """
        for key in self.config.profile:
            image_builder = NUAImageBuilder()
            image_builder.ensure_images(ALLOWED_PROFILE[key])

    def select_base_image(self):
        """Select a base image among possible choices.

        It may append that we have 2 images for Nodejs v14 and v16, and an app
        allowing both version.
        """
        for key, required_version in self.config.profile.items():
            if key == "node":
                self._set_base_image_node(required_version)
        if not self.nua_base:
            self.nua_base = NUA_BUILDER_TAG
        if verbosity(2):
            info(f"Nua base image: '{self.nua_base}'")

    def _set_base_image_node(self, required_version: str):
        references = ALLOWED_PROFILE["node"]
        version_spec = SpecifierSet(required_version)
        for reference in references:
            provided = image_labels(reference).get("node_version")
            if not provided:
                continue
            if Version(provided) in version_spec:
                # we found an image with relevant version of nodejs
                self.nua_base = reference
                return

    def build_docker_image(self):
        self.make_build_dir()
        self.copy_build_files()
        # self.copy_myself()
        if verbosity(1):
            info("Copying Nua config file:", self.config.path.name)
        copy2(self.config.path, self.build_dir)
        self.build_with_docker_stream()
        rm_fr(self.build_dir)

    def make_build_dir(self):
        build_dir_parent = Path(
            config.get("build", {}).get("build_dir", "/var/tmp")  # noqa S108
        )
        if not build_dir_parent.is_dir():
            abort(f"Build directory parent not found: '{build_dir_parent}'")
        self.build_dir = Path(tempfile.mkdtemp(dir=build_dir_parent))
        if verbosity(1):
            info(f"Build directory: {self.build_dir}")

    def detect_nua_dir(self):
        """Detect dir containing nua files (start.py, build.py, Dockerfile,

        ...).
        """
        nua_dir = self.config.build.get("nua_dir")
        if not nua_dir:
            # Check if default 'nua' dir exists
            path = self.config.root_dir / "nua"
            if path.is_dir():
                self.nua_dir = path
            else:
                # Use the root folder (where is the nua-config.toml file)
                self.nua_dir = self.config.root_dir
            return

        # Check if provided path does exists
        path = self.config.root_dir / nua_dir
        if path.is_dir():
            self.nua_dir = path
            return

        abort(f"Path not found (nua_dir) : '{nua_dir}'")

    def copy_from_manifest(self):
        for name in self.config.manifest:
            self._copy_file_from_manifest(name)

    def _copy_file_from_manifest(self, name: str):
        user_file = self.config.root_dir / name
        if user_file.is_file():
            if verbosity(1):
                info("Copying manifest file:", user_file.name)
            copy2(user_file, self.build_dir)
        elif user_file.is_dir():
            if verbosity(1):
                info("Copying manifest directory:", user_file.name)
            copytree(user_file, self.build_dir / name)
        else:
            abort(f"File from manifest not found: {repr(name)}")

    def copy_file_or_dir(self, user_file):
        if user_file.is_file():
            if verbosity(1):
                info("Copying local file:", user_file.name)
            copy2(user_file, self.build_dir)
        elif user_file.is_dir():
            if verbosity(1):
                info("Copying local directory:", user_file.name)
            copytree(user_file, self.build_dir / user_file.name)
        else:
            pass

    def copy_from_local_dir(self):
        """Copy content form local dir: either: root_dir or nua_dir if defined.

        To be fixed for /nua subdir.
        """
        for user_file in self.config.root_dir.glob("*"):
            if (user_file.name).startswith("."):
                continue
            if user_file.name in {NUA_CONFIG, "__pycache__"}:
                continue
            self.copy_file_or_dir(user_file)

    def complete_with_default_files(self):
        """Complete missing files from defaults (Dockerfile, start.py, ...)."""
        for item in rso.files("nua.build.defaults").iterdir():
            if (
                not item.is_file()
                or item.name.startswith("__")
                or item.name.startswith(".")
            ):
                continue
            dest = self.nua_dir / item.name
            print(dest, type(dest))
            if dest.is_file():
                continue
            if verbosity(1):
                info("Copying Nua default file:", item.name)
            content = item.read_text(encoding="utf8")
            target = self.build_dir / self.nua_dir_relative / item.name
            target.write_text(content)

    def copy_build_files(self):
        """Each file of the defaults folder can be replaced by a version
        provided locally by the packager.

        - if some manifest entry, copy files from manifest (of fail)
        - if no manifest entry, copy local files
        - finally, complete by copying files from default if needed
        """
        if self.config.manifest:
            self.copy_from_manifest()
        else:
            self.copy_from_local_dir()
        self.complete_with_default_files()

    @docker_build_log_error
    def build_with_docker(self, save=True):
        if verbosity(2):
            info("Starting build_with_docker()")
        chdir(self.build_dir)
        with suppress(IOError):
            copy2(self.build_dir / self.nua_dir_relative / "Dockerfile", self.build_dir)
        release = self.config.metadata.get("release", "")
        if release:
            rel_tag = f"-{release}"
        else:
            rel_tag = ""
        nua_tag = f"nua-{self.config.app_id}:{self.config.version}{rel_tag}"
        info(f"Building image {nua_tag}")
        client = docker.from_env()
        image, tee = client.images.build(
            path=".",
            tag=nua_tag,
            rm=True,
            forcerm=True,
            buildargs={"nua_builder_tag": self.nua_base},
            labels={
                "APP_ID": self.config.app_id,
                "NUA_TAG": nua_tag,
                "NUA_BUILD_VERSION": __version__,
            },
            nocache=True,
        )
        if verbosity(1):
            display_docker_img(nua_tag)
        if save:
            self.save(image, nua_tag)
        if verbosity(3):
            print("-" * 60)
            print("Build log:")
            print_log_stream(tee)
            print("-" * 60)

    @docker_build_log_error
    def build_with_docker_stream(self, save=True):
        # if verbosity(2):
        #     info("Starting build_with_docker()")
        chdir(self.build_dir)
        with suppress(IOError):
            copy2(self.build_dir / self.nua_dir_relative / "Dockerfile", self.build_dir)
        release = self.config.metadata.get("release", "")
        if release:
            rel_tag = f"-{release}"
        else:
            rel_tag = ""
        nua_tag = f"nua-{self.config.app_id}:{self.config.version}{rel_tag}"
        buildargs = {"nua_builder_tag": self.nua_base}
        labels = {
            "APP_ID": self.config.app_id,
            "NUA_TAG": nua_tag,
            "NUA_BUILD_VERSION": __version__,
        }
        info(f"Building image {nua_tag}")
        image_id = _docker_stream_build(".", nua_tag, buildargs, labels)
        if verbosity(1):
            display_docker_img(nua_tag)
        if save:
            client = docker.from_env()
            image = client.images.get(image_id)
            self.save(image, nua_tag)

    def save(self, image, nua_tag):
        dest = f"/var/tmp/{nua_tag}.tar"  # noqa S108
        with open(dest, "wb") as tarfile:
            for chunk in image.save(chunk_size=2**25, named=True):
                tarfile.write(chunk)
        if verbosity(1):
            show("Docker image saved:")
            info(dest)


def _docker_stream_build(path: str, tag: str, buildargs: dict, labels: dict) -> str:
    client = docker.from_env()
    resp = client.api.build(
        path=path,
        tag=tag,
        rm=True,
        forcerm=True,
        buildargs=buildargs,
        labels=labels,
        nocache=True,
    )
    last_event = None
    image_id = None
    stream = json_stream(resp)
    for chunk in stream:
        if "error" in chunk:
            raise BuildError(chunk["error"], stream)
        last_event = chunk
        message = chunk.get("stream")
        if not message:
            continue
        if match := RE_SUCCESS.search(message):
            image_id = match.group(2)
        if verbosity(2):
            print_stream_blue(message)
    if not image_id:
        raise BuildError(last_event or "Unknown", stream)
    return image_id
