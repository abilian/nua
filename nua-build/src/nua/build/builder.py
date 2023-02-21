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
from pathlib import Path
from shutil import copy2, copytree

import docker
from docker.errors import BuildError
from docker.utils.json_stream import json_stream
from nua.agent.constants import NUA_BUILDER_TAG
from nua.agent.nua_config import NuaConfig, hyphen_get, nua_config_names
from nua.autobuild.docker_build_utils import display_docker_img, docker_build_log_error
from nua.autobuild.nua_image_builder import NUAImageBuilder
from nua.autobuild.register_builders import is_builder
from nua.lib.backports import chdir
from nua.lib.panic import info, show, title, vprint, vprint_blue
from nua.lib.shell import rm_fr
from nua.lib.tool.state import verbosity, verbosity_level

from . import __version__, config

logging.basicConfig(level=logging.INFO)

RE_SUCCESS = re.compile(r"(^Successfully built |sha256:)([0-9a-f]+)$")


class BuilderError(Exception):
    """Builder error."""


class Builder:
    """Class to hold config and other state information during build."""

    container_type: str
    build_dir: Path
    nua_dir: Path
    nua_dir_relative: Path
    manifest: list[Path]
    nua_base: str
    config: NuaConfig

    def __init__(self, config_file):
        self.config = NuaConfig(config_file)
        self.nua_base = ""
        self.manifest = []

    def run(self):
        self.detect_container_type()
        self.check_allowed_base_image()
        self.ensure_base_image_profile_availability()
        self.select_base_image()

        title(f"Building the image for {self.config.app_id}")
        self.detect_nua_dir()
        if self.container_type == "docker":
            self.build_docker_image()
        else:
            raise NotImplementedError(f"Container type '{self.container_type}'")

    def detect_container_type(self):
        """Placeholder for future container technology detection.

        Currently only Docker is supported.
        """
        container = self.config.build.get("container") or "docker"
        if container != "docker":
            raise BuilderError(f"Unknown container type: '{container}'")
        self.container_type = container

    def check_allowed_base_image(self):
        builder = self.config.builder
        if not builder:
            return
        if not is_builder(builder):
            raise BuilderError(f"Unknown Nua builder: '{builder}'")

    def ensure_base_image_profile_availability(self):
        """Profile will determine the required base image.

        If empty, the standard Nua base image is used.
        """
        image_builder = NUAImageBuilder()
        image_builder.ensure_base_image()
        builder = self.config.builder
        if not builder:
            return
        image_builder = NUAImageBuilder()
        image_builder.ensure_images(builder)

    def select_base_image(self):
        """Select a base image among possible choices.

        It may append that we have 2 images for Nodejs v14 and v16, and
        an app allowing both version.
        """
        builder = self.config.builder
        if builder:
            self.nua_base = NUAImageBuilder.builder_tag(builder)
        else:
            self.nua_base = NUA_BUILDER_TAG
        with verbosity(2):
            info(f"Nua base image: '{self.nua_base}'")

    def detect_nua_dir(self):
        """Detect dir containing nua files (start.py, build.py, Dockerfile,
        etc.)."""
        nua_dir = hyphen_get(self.config.build, "nua_dir")
        if not nua_dir:
            # Check if default 'nua' dir exists
            path = self.config.root_dir / "nua"
            if path.is_dir():
                nua_dir = "nua"
            else:
                # Use the root folder (where is the nua-config.toml file)
                nua_dir = "."
        # Check if provided path does exist:
        path = self.config.root_dir / nua_dir
        if not path.is_dir():
            raise BuilderError(f"Path not found for 'nua-dir' : '{nua_dir}'")
        self.nua_dir = path
        self.nua_dir_relative = self.nua_dir.relative_to(self.config.root_dir)
        with verbosity(3):
            vprint(f"self.nua_dir: {self.nua_dir}")
        return

    def build_docker_image(self):
        self.make_build_dir()
        self.list_manifest_files()
        self.copy_manifest_files()
        self.complete_with_default_files()
        with verbosity(1):
            info("Copying Nua config file:", self.config.path.name)
        copy2(self.config.path, self.build_dir)
        self.build_with_docker_stream()
        rm_fr(self.build_dir)

    def make_build_dir(self):
        build_dir_parent = Path(
            config.get("build", {}).get("build_dir", "/var/tmp")  # noqa S108
        )
        if not build_dir_parent.is_dir():
            raise BuilderError(
                f"Build directory parent not found: '{build_dir_parent}'"
            )

        self.build_dir = Path(tempfile.mkdtemp(dir=build_dir_parent))
        with verbosity(1):
            info(f"Build directory: {self.build_dir}")

    def list_manifest_files(self):
        """List the files to copy from local directory."""
        if self.config.manifest:
            self.manifest = [
                self.config.root_dir / name for name in self.config.manifest
            ]
            return
        if self.config.src_url:
            # We have some src_rul defined, so only copy local files from nua_dir
            # (if not defined, it still will be the full local directory)
            if self.nua_dir == self.config.root_dir:
                self.manifest_from_root_dir()
            else:
                self.manifest = [self.nua_dir]
            return
        # Finally, consider that local directory is the source directory: copy all.
        self.manifest_from_root_dir()

    def manifest_from_root_dir(self):
        """Get the list of files and directory without invalid hidden files."""
        with verbosity(3):
            vprint("manifest from:", self.config.root_dir)
        self.manifest = [
            file
            for file in self.config.root_dir.glob("*")
            if not file.name.startswith(".")
            and file.name != "__pycache__"
            and file.name not in list(nua_config_names())
        ]

    def copy_manifest_files(self):
        for file in self.manifest:
            if file.is_file():
                with verbosity(1):
                    info("Copying file:", file.name)
                copy2(file, self.build_dir)
            elif file.is_dir():
                with verbosity(1):
                    info("Copying directory:", file.name)
                copytree(file, self.build_dir / file.name)
            else:
                raise BuilderError(f"File not found: {file}")

    def complete_with_default_files(self):
        """Complete missing files from defaults (Dockerfile, start.py, ...)."""
        if not hyphen_get(self.config.build, "default_files", True):
            return
        for file in rso.files("nua.build.defaults").iterdir():
            if (
                not file.is_file()
                or file.name.startswith("__")
                or file.name.startswith(".")
            ):
                continue
            dest = self.nua_dir / file.name
            if dest.is_file():
                # file already exists, do not replace by default content
                continue
            with verbosity(1):
                info("Copying Nua default file:", file.name)
            content = file.read_text(encoding="utf8")
            target = self.build_dir / self.nua_dir_relative / file.name
            with verbosity(3):
                vprint(f"target path: {target}")
            target.write_text(content)

    @docker_build_log_error
    def build_with_docker_stream(self, save=True):
        with chdir(self.build_dir):
            with suppress(IOError):
                copy2(
                    self.build_dir / self.nua_dir_relative / "Dockerfile",
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
            image_id = _docker_stream_build(".", nua_tag, buildargs, labels)
            with verbosity(1):
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
        with verbosity(1):
            show("Docker image saved:")
            show(dest)


def _print_buffer_log(messages: list[str]):
    for message in messages:
        print(message, end="")


def _docker_stream_build(path: str, tag: str, buildargs: dict, labels: dict) -> str:
    messages_buffer: list[str] = []
    client = docker.from_env()
    resp = client.api.build(
        path=path,
        tag=tag,
        rm=True,
        forcerm=True,
        buildargs=buildargs,
        labels=labels,
        nocache=True,
        timeout=1800,
    )
    last_event = None
    image_id = None
    stream = json_stream(resp)
    for chunk in stream:
        if "error" in chunk:
            _print_buffer_log(messages_buffer)
            raise BuildError(chunk["error"], "")
        last_event = chunk
        message = chunk.get("stream")
        if not message:
            continue
        if match := RE_SUCCESS.search(message):
            image_id = match.group(2)
        with verbosity(2):
            vprint_blue(message)
        if verbosity_level() < 2:
            # store message for printing full log if later an error occurs
            messages_buffer.append(message)
    if not image_id:
        _print_buffer_log(messages_buffer)
        raise BuildError(last_event or "Unknown", "")
    return image_id
