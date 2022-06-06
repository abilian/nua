#!/bin/env python3
"""Command to generate the base Nua docker image.

command: "nuad generate_nua_docker"

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""

from os import chdir
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

import docker
import typer

from ..constants import BUILD, DOCKER_FILE, MYSELF_DIR, NUA_TAG
from ..docker_utils import display_docker_img, docker_build_log_error
from ..scripting import *

assert MYSELF_DIR.is_dir()


app = typer.Typer()


@docker_build_log_error
def build_with_docker(build_dir, iname):
    chdir(build_dir)
    print(f"Building image {iname} (it may take a while...)")
    client = docker.from_env()
    client.images.build(path=".", tag=iname, rm=True, forcerm=True)
    # cmd = f"docker build -t {name} ."
    # sh(cmd)


def copy_myself(build_dir):
    print("Copying nua_build python code")
    copytree(
        MYSELF_DIR,
        build_dir / "nua_build",
        ignore=ignore_patterns("*.pyc", "__pycache__"),
    )


@app.command("build_nua_docker")
def generate_nua_docker_cmd() -> None:
    """build the base Nua docker image."""

    print_green(f"*** Generation of the docker image {NUA_TAG} ***")
    build_dir = Path.cwd() / BUILD
    rm_fr(build_dir)
    mkdir_p(build_dir)
    copy2(DOCKER_FILE, build_dir)
    copy_myself(build_dir)
    build_with_docker(build_dir, NUA_TAG)
    display_docker_img(NUA_TAG)
    # sh("docker image ls nua_base")
