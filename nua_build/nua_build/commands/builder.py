"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""
import logging
from contextlib import suppress
from os import chdir
from pathlib import Path
from shutil import copy2, copytree

import docker

from .. import __version__, config
from ..constants import (
    BUILD,
    DEFAULTS_DIR,
    MYSELF_DIR,
    NUA_BUILDER_TAG,
    NUA_CONFIG,
    NUA_WHEEL_DIR,
)
from ..docker_utils_build import display_docker_img, docker_build_log_error
from ..nua_config import NuaConfig
from ..panic import error
from ..rich_console import print_green
from ..shell import mkdir_p, rm_fr
from ..state import verbosity
from .build_nua_builder import build_nua_builder

# import typer


# from typing import Optional


assert MYSELF_DIR.is_dir()

logging.basicConfig(level=logging.INFO)

# app = typer.Typer()


class Builder:
    """Class to hold config and other state information during build."""

    def __init__(self, config_file):
        # wether the config file is local or not, use local dir for build:
        self.work_dir = Path.cwd()
        build_dir_parent = config.get("build", {}).get("build_dir", self.work_dir)
        self.build_dir = Path(build_dir_parent) / BUILD
        self.config = NuaConfig(config_file)
        self.container_type = ""
        self.nua_dir = None
        self.nua_dir_relative = None

    def run(self):
        self.detect_container_type()
        self.detect_nua_dir()
        self.nua_dir_relative = self.nua_dir.relative_to(self.config.root_dir)
        if self.container_type == "docker":
            self.setup_build_directory()
            self.build_with_docker()

    def detect_container_type(self):
        """Placeholder for future container technology detection.

        Currently only Docker is supported.
        """
        container = self.config.build.get("container") or "docker"
        if container != "docker":
            error(f"Unknown container type : '{container}'")
        self.container_type = container

    def detect_nua_dir(self):
        """Detect dir containing nua files (start.py, build.py, Dockerfile, ...)."""
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
        path = self.config.root_dir / Path(nua_dir)
        if path.is_dir():
            self.nua_dir = path
            return
        error(f"Path not found (nua_dir) : '{nua_dir}'")

    def setup_build_directory(self):
        if verbosity(2):
            print(f"build dir: {self.build_dir}")
        rm_fr(self.build_dir)
        mkdir_p(self.build_dir)
        self.copy_build_files()
        # self.copy_myself()
        if verbosity(1):
            print("Copying Nua config file:", self.config.path.name)
        copy2(self.config.path, self.build_dir)
        # chown_r(self.build_dir, user, group)  # todo

    def copy_from_manifest(self):
        for name in self.config.manifest:
            user_file = self.config.root_dir / name
            if user_file.is_file():
                if verbosity(1):
                    print("Copying manifest file:", user_file.name)
                copy2(user_file, self.build_dir)
            elif user_file.is_dir():
                if verbosity(1):
                    print("Copying manifest directory:", user_file.name)
                copytree(user_file, self.build_dir / name)
            else:
                error(f"File from manifest not found: {repr(name)}")

    def copy_file_or_dir(self, user_file):
        if user_file.is_file():
            if verbosity(1):
                print("Copying local file:", user_file.name)
            copy2(user_file, self.build_dir)
        elif user_file.is_dir():
            if verbosity(1):
                print("Copying local directory:", user_file.name)
            copytree(user_file, self.build_dir / user_file.name)
        else:
            pass

    def copy_from_local_dir(self):
        for user_file in self.config.root_dir.glob("*"):
            if (user_file.name).startswith("."):
                continue
            if user_file.name in {BUILD, NUA_CONFIG, "__pycache__"}:
                continue
            self.copy_file_or_dir(user_file)

    def complete_with_default_files(self):
        """Complete missing files from defaults (Dockerfile, start.py, ...)."""
        for default_file in DEFAULTS_DIR.glob("*"):
            if (default_file.name).startswith("."):
                continue
            if not default_file.is_file():
                continue
            self._complete_with_file(default_file)

    def _complete_with_file(self, default_file: Path):
        dest = self.nua_dir / default_file.name
        if dest.is_file():
            return
        if verbosity(1):
            print("Copying Nua default file:", default_file.name)
        copy2(default_file, self.build_dir / self.nua_dir_relative)

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
            print("Starting build_with_docker()")
        chdir(self.build_dir)
        with suppress(IOError):
            copy2(self.build_dir / self.nua_dir_relative / "Dockerfile", self.build_dir)
        release = self.config.metadata.get("release", "")
        rel_tag = f"-{release}" if release else ""
        nua_tag = f"nua-{self.config.app_id}:{self.config.version}{rel_tag}"
        print_green(f"Building image {nua_tag}")
        client = docker.from_env()
        image, tee = client.images.build(
            path=".",
            tag=nua_tag,
            rm=True,
            forcerm=True,
            buildargs={"nua_builder_tag": NUA_BUILDER_TAG},
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

    def save(self, image, nua_tag):
        dest = f"/var/tmp/{nua_tag}.tar"
        with open(dest, "wb") as tarfile:
            for chunk in image.save(named=True):
                tarfile.write(chunk)
        if verbosity(1):
            print("Docker image saved:")
            print(dest)


def _check_nua_build_wheel() -> bool:
    if not NUA_WHEEL_DIR.is_dir() or not list(NUA_WHEEL_DIR.glob("nua_build*.whl")):
        if verbosity(1):
            message = f"Python wheel for '{NUA_BUILDER_TAG}' not found locally\n"
            print(message)
            message = f"[fixme]: Make new installation of the package with ./build.sh"
            error(message)
        return False
    return True


def _check_nua_build_docker_image() -> bool:
    client = docker.from_env()
    result = bool(client.images.list(filters={"reference": NUA_BUILDER_TAG}))
    if not result:
        if verbosity(1):
            message = (
                f"Docker image '{NUA_BUILDER_TAG}' not found locally, build required."
            )
            print(message)
    return result


def build_nua_builder_if_needed():
    if not _check_nua_build_wheel() or not _check_nua_build_docker_image():
        build_nua_builder()


# @app.command("build")
# @app.command()
# def build_cmd(
#     config_file: Optional[str] = argument_config,
#     verbose: bool = option_verbose,
# ) -> None:
#     """Build Nua package from some 'nua-config.toml' file."""
#     # first build the nua_base image if needed
#     build_nua_builder_if_needed(verbose)
#     builder = Builder(config_file, verbose)
#     print_green(f"*** Generation of the docker image for {builder.config.app_id} ***")
#     builder.setup_build_directory()
#     builder.build_with_docker()
