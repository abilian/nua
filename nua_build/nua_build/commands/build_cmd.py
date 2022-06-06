#!/bin/env python3
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
from shutil import copy2, copytree, ignore_patterns

import docker
import typer

from ..constants import BUILD, DEFAULTS_DIR, MYSELF_DIR, NUA_TAG
from ..docker_utils import display_docker_img, docker_build_log_error
from ..nua_config import NuaConfig
from ..scripting import *

assert MYSELF_DIR.is_dir()

logging.basicConfig(level=logging.INFO)

app = typer.Typer()


class Builder:
    """Class to hold config and other state information during build."""

    def __init__(self):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        self.root_dir = Path.cwd()
        self.build_dir = self.root_dir / BUILD
        # if the nua-config.toml file is not found locally, it aborts build process
        self.config = NuaConfig()

    def setup_build_directory(self):
        rm_fr(self.build_dir)
        mkdir_p(self.build_dir)
        self.copy_build_files()
        self.copy_myself()
        print("Copying config file:", self.config.path.name)
        copy2(self.config.path, self.build_dir)
        # chown_r(self.build_dir, user, group)  # todo

    def copy_build_files(self):
        """Each file of the defaults folder can be replaced by a version
        provided locally by the packager.

        - if some manifest entry, copy files from manifest (of fail)
        - if no manifest entry, copy local files
        - finally, complete by copying files from default if needed
        """
        copied_files = set()
        if self.config.manifest:
            for name in self.config.manifest:
                print("Copying manifest file:", name)
                user_file = self.root_dir / name
                if user_file.is_file():
                    copy2(user_file, self.build_dir)
                elif user_file.is_dir():
                    copytree(user_file, self.build_dir)
                else:
                    panic(f"File from manifest not found: {repr(name)}")
                copied_files.add(name)
        else:  # copy local files
            for user_file in self.root_dir.glob("*"):
                if (user_file.name).startswith("."):
                    continue
                print("Copying local file:", user_file.name)
                if user_file.is_file():
                    copy2(user_file, self.build_dir)
                elif user_file.is_dir():
                    copytree(user_file, self.build_dir)
                else:
                    panic(f"File from manifest not found: {repr(name)}")
                copied_files.add(user_file.name)
        # complete with default files:
        for default_file in DEFAULTS_DIR.glob("*"):
            if (default_file.name).startswith(".") or not default_file.is_file():
                continue
            if default_file.name in copied_files:
                continue
            print("Copying Nua default file:", default_file.name)
            copy2(default_file, self.build_dir)

    def copy_myself(self):
        print("Copying Nua_build python package")
        copytree(
            MYSELF_DIR,
            self.build_dir / "nua_build",
            ignore=ignore_patterns("*.pyc", "__pycache__"),
        )

    @docker_build_log_error
    def build_with_docker(self):
        chdir(self.build_dir)
        iname = f"nua_{self.config.app_id}:{self.config.version}"
        print_green(f"Building image {iname}")
        client = docker.from_env()
        client.images.build(
            path=".",
            tag=iname,
            rm=True,
            forcerm=True,
            buildargs={"nua_base_version": NUA_TAG},
        )
        display_docker_img(iname)


def build_nua_base_if_needed():
    client = docker.from_env()
    result = client.images.list(filters={"reference": NUA_TAG})
    if not result:
        print(f"Image '{NUA_TAG}' not found: build required.")
        sh("nuad build_nua_docker")


@app.command("build")
def build_cmd() -> None:
    """Build Nua package, using local 'nua-config.toml' file."""
    # first build the nua_base image if needed
    build_nua_base_if_needed()
    builder = Builder()
    print_green(f"*** Generation of the docker image for {builder.config.app_id} ***")
    builder.setup_build_directory()
    builder.build_with_docker()
    #
    # if config.src_url:
    #     sh(f"curl -sL {config.src_url} | tar -xz -c src --strip-components 1 -f -")
    # elif config.src_git:
    #     sh(f"git clone {config.src_git} src")
    # else:
    #     raise Exception("Missing src_url or src_git")
    #
    # if is_python_project():
    #     build_python()
