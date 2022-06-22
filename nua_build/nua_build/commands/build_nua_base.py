"""script to build the Nua base image."""
from os import chdir
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

import docker
import typer

from .. import __version__ as nua_version
from .. import config
from ..constants import (
    BUILD,
    DOCKERFILE_MIN,
    DOCKERFILE_NUA_BASE,
    MYSELF_DIR,
    NUA_BASE_TAG,
    NUA_MIN_TAG,
)
from ..db import store
from ..docker_utils import (
    display_docker_img,
    docker_build_log_error,
    image_created_as_iso,
    print_log_stream,
)
from ..rich_console import print_green
from ..shell import mkdir_p, rm_fr

app = typer.Typer()

option_verbose = typer.Option(False, help="Print build log.")


def build_nua_base(verbose):
    print_green(f"*** Generation of the docker image {NUA_BASE_TAG} ***")
    build_minimal_layer(verbose)
    build_base_layer(verbose)


def set_build_dir(orig_wd):
    build_dir_parent = config.get("nua", "build", "build_dir") or orig_wd
    build_dir = Path(build_dir_parent) / BUILD
    rm_fr(build_dir)
    mkdir_p(build_dir)
    return build_dir


def build_minimal_layer(verbose):
    orig_wd = Path.cwd()
    build_dir = set_build_dir(orig_wd)
    copy2(DOCKERFILE_MIN, build_dir)
    docker_build_minimal(build_dir, verbose)
    display_docker_img(NUA_MIN_TAG)
    chdir(orig_wd)


@docker_build_log_error
def docker_build_minimal(build_dir, verbose=False):
    chdir(build_dir)
    print(f"1/2: Building image {NUA_MIN_TAG}")
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_MIN).name,
        tag=NUA_MIN_TAG,
        rm=False,
    )
    # no data, actually not activable, it's on only a requisite.
    store.store_image(
        id_sha=image.id,
        app_id="nua-min",
        nua_tag=NUA_MIN_TAG,
        created=image_created_as_iso(image),
        size=image.attrs["Size"],
        nua_version=nua_version,
        instance="",
        data=None,
    )
    if verbose:
        print_log_stream(tee)


def build_base_layer(verbose):
    orig_wd = Path.cwd()
    build_dir = set_build_dir(orig_wd)
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
    image, tee = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_NUA_BASE).name,
        buildargs={"nua_min_tag": NUA_MIN_TAG, "nua_version": nua_version},
        tag=NUA_BASE_TAG,
        rm=False,
    )
    store.store_image(
        id_sha=image.id,
        app_id="nua-base",
        nua_tag=NUA_BASE_TAG,
        created=image_created_as_iso(image),
        size=image.attrs["Size"],
        nua_version=nua_version,
        instance="",
        data=None,
    )
    if verbose:
        print_log_stream(tee)


def copy_myself(build_dir):
    print("Copying nua_build python code")
    copytree(
        MYSELF_DIR,
        build_dir / f"nua_build_{nua_version}",  # fix cache issues
        ignore=ignore_patterns("*.pyc", "__pycache__", "_build"),
    )


@app.command("build_nua_docker")
def generate_nua_docker_cmd(verbose: bool = option_verbose) -> None:
    """build the base Nua docker image."""
    build_nua_base(verbose)
