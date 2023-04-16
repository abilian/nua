"""Builder class, core of build process.

Builder instance maintains config and other state information during build.

Typical use::

    builder = get_builder(config_file)
    builder.run()
"""
from __future__ import annotations

import abc
import logging
import tempfile
from abc import abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from importlib import resources as rso
from pathlib import Path
from pprint import pformat
from shutil import copy2, copytree

import docker
from docker.models.images import Image

from nua.agent.constants import NUA_BUILDER_TAG
from nua.agent.nua_config import NuaConfig, hyphen_get, nua_config_names
from nua.autobuild.docker_build_utils import (
    display_docker_img,
    docker_build_log_error,
    docker_stream_build,
)
from nua.autobuild.nua_image_builder import NuaImageBuilder
from nua.autobuild.register_builders import is_builder
from nua.lib.backports import chdir
from nua.lib.panic import info, show, title, vfprint, vprint
from nua.lib.shell import rm_fr
from nua.lib.tool.state import verbosity, verbosity_level

from . import __version__, config

logging.basicConfig(level=logging.INFO)
CLIENT_TIMEOUT = 600


class BuilderError(Exception):
    """Builder error."""


def get_builder(config_path: str | Path | None = None) -> Builder:
    config = NuaConfig(config_path)
    factory = BuilderFactory(config)
    return factory.get_builder()


@dataclass(frozen=True)
class BuilderFactory:
    """Factory to create a Builder instance."""

    config: NuaConfig

    def get_builder(self) -> Builder:
        with verbosity(4):
            vprint(pformat(self.config.as_dict()))

        # Not used at this stage
        # container_type = self.detect_container_type()
        build_method = self.detect_build_method()

        if build_method == "build":
            return DockerBuilder(self.config)

        if build_method == "wrap":
            return DockerWrapBuilder(self.config)

        raise ValueError(
            f"Unknown build strategy '{build_method}'"
        )

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

    def _title_build(self):
        title(f"Building the image for {self.config.app_id}")

    def make_build_dir(self) -> Path:
        build_dir_parent = Path(
            config.get("build", {}).get("build_dir", "/var/tmp")  # noqa S108
        )
        if not build_dir_parent.is_dir():
            raise BuilderError(
                f"Build directory parent not found: '{build_dir_parent}'"
            )

        with verbosity(1):
            info(f"Build directory: {self.build_dir}")

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


class DockerBuilder(Builder):
    # FIXME later
    container_type = "docker"

    def run(self):
        self.check_allowed_base_image()
        self.ensure_base_image_profile_availability()
        self.select_base_image()
        self._title_build()
        self.detect_nua_folder()
        if self.container_type == "docker":
            self.build_docker_image()
        else:
            raise NotImplementedError(f"Container type '{self.container_type}'")

    def check_allowed_base_image(self):
        builder = self.config.builder
        if not builder:
            return
        if not is_builder(builder):
            raise BuilderError(f"Unknown Nua builder: '{builder}'")

    def ensure_base_image_profile_availability(self):
        """Ensure the required Nua images are available.

        The tag 'builder' will determine the required base image. If
        empty, the standard Nua base image is used.
        """
        image_builder = NuaImageBuilder()
        image_builder.ensure_images(self.config.builder)

    def select_base_image(self):
        """Select a base image among possible choices.

        It may append that we have 2 images for Node.js v14 and v16, and
        an app allowing both version.
        """
        builder = self.config.builder
        if builder:
            self.nua_base = NuaImageBuilder.builder_tag(builder)
        else:
            self.nua_base = NUA_BUILDER_TAG
        with verbosity(2):
            info(f"Nua base image: '{self.nua_base}'")

    def detect_nua_folder(self):
        """Detect folder containing nua files.

        (Dockerfile, start.py, build.py, ...)
        """
        if self.config.nua_dir_exists:
            self.nua_folder = self.config.root_dir / "nua"
        else:
            self.nua_folder = self.config.root_dir

    def build_docker_image(self):
        self.copy_project_files()
        with verbosity(1):
            info("Copying Nua config file:", self.config.path.name)
        copy2(self.config.path, self.build_dir)
        self.build_with_docker_stream()
        rm_fr(self.build_dir)

    def copy_project_files(self):
        """Detect and copy files to build_dir.

        - if no 'src-url', copy local source code from root_dir into build_dir
        - if 'src-url' or other remote source, do not copy local code of root_dir
        - if 'manifest' defined, copy manifest content to nua/src
        - if /nua exists, copy it to nua (but not nua/src or nua-config)
        - then copy required/default files to build_dir (nuaconfig, ...)
        """
        (self.build_dir / "nua").mkdir(mode=0o755)
        self._copy_local_code()
        self._copy_manifest_files()
        self._copy_nua_folder()
        self._copy_default_files()

    @docker_build_log_error
    def build_with_docker_stream(self, save: bool = True):
        with chdir(self.build_dir):
            with suppress(IOError):
                copy2(
                    self.build_dir / "nua" / "Dockerfile",
                    self.build_dir,
                )
            nua_tag = self.config.nua_tag
            buildargs = {
                "nua_builder_tag": self.nua_base,
                "nua_verbosity": str(verbosity_level()),
            }
            labels = {
                "APP_ID": self.config.app_id,
                "NUA_TAG": nua_tag,
                "NUA_BUILD_VERSION": __version__,
            }
            info(f"Building image {nua_tag}")
            image_id = docker_stream_build(".", nua_tag, buildargs, labels)

            with verbosity(1):
                display_docker_img(nua_tag)

            if save:
                client = docker.from_env(timeout=CLIENT_TIMEOUT)
                image = client.images.get(image_id)
                self.save(image, nua_tag)

    def _copy_local_code(self):
        if any((self.config.src_url, self.config.git_url)):
            return
        files = [
            item
            for item in self.config.root_dir.glob("*")
            if not item.name.startswith(".")
            and item.name != "__pycache__"
            and item.name != "nua"
            and item.name not in set(nua_config_names())
        ]
        self._copy_items(files, self.build_dir)

    def _copy_manifest_files(self):
        if not self.config.manifest:
            return
        files = [self.config.root_dir / name for name in self.config.manifest]
        self._copy_items(files, self.build_dir)

    def _copy_nua_folder(self):
        if not self.config.nua_dir_exists:
            return
        files = [
            item
            for item in (self.config.root_dir / "nua").glob("*")
            if not item.name.startswith(".")
            and item.name not in set(nua_config_names())
        ]
        self._copy_items(files, self.build_dir / "nua")

    def _copy_items(self, paths: list[Path], dest_dir: Path):
        for path in paths:
            if path.is_file():
                with verbosity(1):
                    info("Copying file:", path.name)
                copy2(path, dest_dir)
            elif path.is_dir():
                with verbosity(1):
                    info("Copying directory:", path.name)
                copytree(path, dest_dir / path.name, dirs_exist_ok=True)
            else:
                raise BuilderError(f"File not found: {path}")

    def _copy_default_files(self):
        """Complete missing files from defaults, at the moment the Dockerfile,
        (and maybe start.py, ...)."""
        if not hyphen_get(self.config.build, "default_files", True):
            return
        for file in rso.files("nua.build.defaults").iterdir():
            if (
                not file.is_file()
                or file.name.startswith("__")
                or file.name.startswith(".")
            ):
                continue

            path = self.nua_folder / file.name
            destination = self.build_dir / "nua" / file.name
            if path.is_file():
                # file already exists, do not replace by default content, but copy
                # to /nua
                if path != destination:
                    copy2(path, self.build_dir / "nua")
                continue

            with verbosity(1):
                info("Copying Nua default file:", file.name)

            content = file.read_text(encoding="utf8")
            destination = self.build_dir / "nua" / file.name

            with verbosity(3):
                vprint(f"destination path: {destination}")

            destination.write_text(content)


class DockerWrapBuilder(Builder):
    def run(self):
        self._title_build()
        # FIXME:
        # if self.container_type != "docker":
        #     raise NotImplementedError(f"Container type '{self.container_type}'")
        self.write_wrap_dockerfile()
        self.build_wrap_with_docker_stream()
        rm_fr(self.build_dir)

    def write_wrap_dockerfile(self):
        self.config.dump_json(self.build_dir)
        docker_file = self.build_dir / "Dockerfile"
        if self.config.docker_user:
            content = (
                "ARG nua_wrap_tag\n"
                "FROM ${nua_wrap_tag}\n\n"
                "USER root\n"
                "RUN mkdir -p /nua/metadata\n"
                "COPY nua-config.json /nua/metadata/\n"
                f"USER {self.config.docker_user}\n"
            )
        else:
            content = (
                "ARG nua_wrap_tag\n"
                "FROM ${nua_wrap_tag}\n\n"
                "RUN mkdir -p /nua/metadata\n"
                "COPY nua-config.json /nua/metadata/\n"
            )
        docker_file.write_text(content, encoding="utf8")

    @docker_build_log_error
    def build_wrap_with_docker_stream(self, save: bool = True):
        with chdir(self.build_dir):
            nua_tag = self.config.nua_tag
            buildargs = {
                "nua_wrap_tag": self.config.wrap_image,
            }
            labels = {
                "APP_ID": self.config.app_id,
                "NUA_TAG": nua_tag,
                "NUA_BUILD_VERSION": __version__,
            }
            info(f"Building (wrap) image {nua_tag}")
            image_id = docker_stream_build(".", nua_tag, buildargs, labels)

            with verbosity(1):
                display_docker_img(nua_tag)

            if save:
                client = docker.from_env(timeout=CLIENT_TIMEOUT)
                image = client.images.get(image_id)
                self.save(image, nua_tag)
