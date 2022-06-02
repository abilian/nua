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

from .nua_config import NuaConfig
from .scripting import is_python_project, mkdir_p, panic, rm_fr, sh

BUILD = "_build"
DEFAULTS_DIR = Path(__file__).parent.parent / "defaults"
MYSELF_DIR = Path(__file__).parent.parent.parent
assert DEFAULTS_DIR.is_dir()
assert MYSELF_DIR.is_dir()

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
                if not user_file.is_file():  # fixme: see later for directories
                    panic(f"File from manifest not found: {repr(name)}")
                copy2(user_file, self.build_dir)
                copied_files.add(name)
        else:  # copy local files
            for user_file in self.root_dir.glob("*"):
                if (user_file.name).startswith(".") or not user_file.is_file():
                    continue
                print("Copying local file:", user_file.name)
                copy2(user_file, self.build_dir)
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
            f"docker build -t {self.config.app_id}:{self.config.version} ."
        )
        sh(cmd)


@app.command("build")
def build_cmd() -> None:
    """Build package, using local 'nua-config.toml' file."""

    builder = Builder()
    # builder.pip_list()  # for check during devel
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
