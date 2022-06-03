#!/bin/env python3
"""Command to generate the base Nua docker image.

command: "nuad generate_nua_docker"

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""

from os import chdir
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

import typer

from ..scripting import *
from ..version import __version__

BUILD = "_build"
DOCKER_FILE = Path(__file__).parent.parent / "nua_docker_file" / "Dockerfile"
MYSELF_DIR = Path(__file__).parent.parent.parent
assert MYSELF_DIR.is_dir()


app = typer.Typer()


def build_with_docker(build_dir):
    chdir(build_dir)
    name = f"nua_base:{__version__}"
    cmd = f"docker build -t {name} ."
    sh(cmd)


def copy_myself(build_dir):
    print("Copying Nua_build python app.")
    copytree(
        MYSELF_DIR,
        build_dir / "nua_build",
        ignore=ignore_patterns("*.pyc", "__pycache__"),
    )


@app.command("build_nua_docker")
def generate_nua_docker_cmd() -> None:
    """build the base Nua docker image."""

    print_green("*** Generation of the Nua base docker image ***")
    build_dir = Path.cwd() / BUILD
    rm_fr(build_dir)
    mkdir_p(build_dir)
    copy2(DOCKER_FILE, build_dir)
    copy_myself(build_dir)
    build_with_docker(build_dir)
    sh("docker image ls nua_base")
