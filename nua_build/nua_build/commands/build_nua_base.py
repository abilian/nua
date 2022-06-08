"""script to build the Nua base image.
"""
from os import chdir
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

import docker
import typer

from .. import __version__ as nua_version
from ..constants import (
    BUILD,
    DOCKERFILE_MIN,
    DOCKERFILE_NUA_BASE,
    MYSELF_DIR,
    NUA_BASE_TAG,
    NUA_MIN_TAG,
)
from ..docker_utils import display_docker_img, docker_build_log_error, print_log_stream
from ..scripting import *

app = typer.Typer()


def build_nua_base(verbose):
    print_green(f"*** Generation of the docker image {NUA_BASE_TAG} ***")
    build_minimal_layer(verbose)
    build_base_layer(verbose)


def build_minimal_layer(verbose):
    orig_wd = Path.cwd()
    build_dir = orig_wd / BUILD
    rm_fr(build_dir)
    mkdir_p(build_dir)
    copy2(DOCKERFILE_MIN, build_dir)
    docker_build_minimal(build_dir, verbose)
    display_docker_img(NUA_MIN_TAG)
    chdir(orig_wd)


@docker_build_log_error
def docker_build_minimal(build_dir, verbose=False):
    chdir(build_dir)
    print(f"1/2: Building image {NUA_MIN_TAG}")
    client = docker.from_env()
    result = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_MIN).name,
        tag=NUA_MIN_TAG,
        rm=False,
    )
    if verbose:
        print_log_stream(result[1])


def build_base_layer(verbose):
    orig_wd = Path.cwd()
    build_dir = orig_wd / BUILD
    rm_fr(build_dir)
    mkdir_p(build_dir)
    copy2(DOCKERFILE_NUA_BASE, build_dir)
    copy_myself(build_dir)
    docker_build_base(build_dir, verbose)
    display_docker_img(NUA_BASE_TAG)
    chdir(orig_wd)


@docker_build_log_error
def docker_build_base(build_dir, verbose=False):
    chdir(build_dir)
    print(f"2/2: Building image {NUA_BASE_TAG} (it may take a while...)")
    client = docker.from_env()
    result = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_NUA_BASE).name,
        buildargs={"nua_min_tag": NUA_MIN_TAG, "nua_version": nua_version},
        tag=NUA_BASE_TAG,
        rm=False,
    )
    if verbose:
        print_log_stream(result[1])


def copy_myself(build_dir):
    print("Copying nua_build python code")
    copytree(
        MYSELF_DIR,
        build_dir / f"nua_build_{nua_version}",  # fix cache issues
        ignore=ignore_patterns("*.pyc", "__pycache__"),
    )


@app.command("build_nua_docker")
def generate_nua_docker_cmd(
    verbose: bool = typer.Option(False, help="Print build log.")
) -> None:
    """build the base Nua docker image."""
    build_nua_base(verbose)
