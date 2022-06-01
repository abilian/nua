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
from shutil import copy2

import typer

from .nua_config import NuaConfig
from .scripting import is_python_project, mkdir_p, rm_fr, sh

BUILD = "_build"
DEFAULTS_DIR = Path(__file__).parent.parent / "defaults"
assert DEFAULTS_DIR.is_dir()

logging.basicConfig(level=logging.INFO)

app = typer.Typer()


def build_python():
    sh("python3 -m venv /nua/env")
    if Path("requirements.txt").exists():
        sh("/nua/env/bin/pip install -r src/requirements.txt")
    elif Path("setup.py").exists():
        sh("/nua/env/bin/pip install src")


class Builder:
    """Class to hold config and other state information during build."""

    def __init__(self):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        self.root_dir = Path.cwd()
        self.build_dir = Path.cwd() / BUILD
        # if the nua-config.toml file is not found locally, it aborts build process
        self.config = NuaConfig()

    def pip_list(self):
        sh("pip list")

    def setup_build_directory(self):
        rm_fr(self.build_dir)
        mkdir_p(self.build_dir)
        self.copy_scripts()
        copy2(self.config.path, self.build_dir)
        # chown_r(self.build_dir, user, group)  # todo

    def copy_scripts(self):
        """Each file of the defaults folder can be replaced by a version
        provided locally by the packager."""
        for default_file in DEFAULTS_DIR.glob("*"):
            print(default_file.name)
            user_file = self.root_dir / default_file.name
            if user_file.is_file():
                copy2(user_file, self.build_dir)
            else:
                copy2(default_file, self.build_dir)

    def build_with_docker(self):
        chdir(self.root_dir)  # security
        sh(
            f"cd {BUILD} && docker build -t {self.config.app_id}:{self.config.version} ."
        )


@app.command("build")
def build_cmd() -> None:
    """Build package, using local 'nua-config.toml' file."""

    builder = Builder()
    builder.pip_list()  # for check during devel
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
