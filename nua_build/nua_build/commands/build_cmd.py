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

import typer

from ..nua_config import NuaConfig
from ..scripting import *
from ..version import __version__

BUILD = "_build"
DEFAULTS_DIR = Path(__file__).parent.parent / "defaults"
MYSELF_DIR = Path(__file__).parent.parent.parent
assert DEFAULTS_DIR.is_dir()
assert MYSELF_DIR.is_dir()

logging.basicConfig(level=logging.INFO)

app = typer.Typer()


class Builder:
    """Class to hold config and other state information during build."""

    def __init__(self):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        self.root_dir = Path.cwd()
        self.build_dir = Path.cwd() / BUILD
        # if the nua-config.toml file is not found locally, it aborts build process
        self.config = NuaConfig()

    def setup_build_directory(self):
        rm_fr(self.build_dir)
        mkdir_p(self.build_dir)
        self.copy_build_files()
        self.copy_myself()
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
        print("Copying Nua_build python app.")
        copytree(
            MYSELF_DIR,
            self.build_dir / "nua_build",
            ignore=ignore_patterns("*.pyc", "__pycache__"),
        )

    def build_with_docker(self):
        chdir(self.root_dir)  # security
        cmd = (
            f"cd {BUILD} && "
            f"docker build --build-arg nua_version={__version__} "
            f"-t {self.config.app_id}:{self.config.version} ."
        )
        sh(cmd)


def build_nua_base_if_needed():
    name = f"nua_base:{__version__}"
    cmd = (
        f"docker image inspect {name} >/dev/null 2>&1 || "
        "nuad build_nua_docker; exit 0"
    )
    sh(cmd)


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
