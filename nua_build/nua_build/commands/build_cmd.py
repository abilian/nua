"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""
import logging
from os import chdir
from pathlib import Path
from shutil import copy2, copytree

import docker

from .. import __version__, config
from ..constants import BUILD, DEFAULTS_DIR, MYSELF_DIR, NUA_BUILDER_TAG, NUA_CONFIG
from ..docker_utils_build import display_docker_img, docker_build_log_error
from ..nua_config import NuaConfig
from ..panic import error
from ..rich_console import print_green
from ..shell import mkdir_p, rm_fr
from .build_nua_builder import build_nua_builder

# import typer


# from typing import Optional


assert MYSELF_DIR.is_dir()

logging.basicConfig(level=logging.INFO)

# app = typer.Typer()


class Builder:
    """Class to hold config and other state information during build."""

    def __init__(self, config_file, verbose=False):
        # wether the config file is local or not, use local dir fior build:
        self.work_dir = Path.cwd()
        build_dir_parent = config.get("build", {}).get("build_dir", self.work_dir)
        self.build_dir = Path(build_dir_parent) / BUILD
        self.config = NuaConfig(config_file)
        self.copied_files = set()
        self.verbose = verbose

    def setup_build_directory(self):
        rm_fr(self.build_dir)
        mkdir_p(self.build_dir)
        self.copy_build_files()
        # self.copy_myself()
        print("Copying config file:", self.config.path.name)
        copy2(self.config.path, self.build_dir)
        # chown_r(self.build_dir, user, group)  # todo

    def copy_from_manifest(self):
        for name in self.config.manifest:
            user_file = self.config.root_dir / name
            if user_file.is_file():
                print("Copying manifest file:", user_file.name)
                copy2(user_file, self.build_dir)
            elif user_file.is_dir():
                print("Copying manifest directory:", user_file.name)
                copytree(user_file, self.build_dir / name)
            else:
                error(f"File from manifest not found: {repr(name)}")
            self.copied_files.add(name)

    def copy_file_or_dir(self, user_file):
        if user_file.is_file():
            print("Copying local file:", user_file.name)
            copy2(user_file, self.build_dir)
            self.copied_files.add(user_file.name)
        elif user_file.is_dir():
            print("Copying local directory:", user_file.name)
            copytree(user_file, self.build_dir / user_file.name)
            self.copied_files.add(user_file.name)
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
        for default_file in DEFAULTS_DIR.glob("*"):
            if (default_file.name).startswith("."):
                continue
            if not default_file.is_file():
                continue
            if default_file.name in self.copied_files:
                continue
            print("Copying Nua default file:", default_file.name)
            copy2(default_file, self.build_dir)

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
        chdir(self.build_dir)
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
        display_docker_img(nua_tag)
        if save:
            self.save(image, nua_tag)

    def save(self, image, nua_tag):
        dest = f"/var/tmp/{nua_tag}.tar"
        with open(dest, "wb") as tarfile:
            for chunk in image.save(named=True):
                tarfile.write(chunk)
        print("Docker image saved:")
        print(dest)


def build_nua_builder_if_needed(verbose):
    found = False
    client = docker.from_env()
    result = client.images.list(filters={"reference": NUA_BUILDER_TAG})
    if result:
        found = True
    else:
        message = f"Image '{NUA_BUILDER_TAG}' not found locally: build required."
    if not found:
        print(message)
        build_nua_builder(verbose)


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
