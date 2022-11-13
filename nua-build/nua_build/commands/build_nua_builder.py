"""Script to build the Nua base image (the nua runtime image)."""
import tempfile
from os import chdir
from pathlib import Path
from shutil import copy2

import docker
import typer

from .. import __version__ as nua_version
from .. import config
from ..common.panic import error
from ..common.rich_console import print_green
from ..common.shell import mkdir_p, rm_fr
from ..constants import (
    DOCKERFILE_BUILDER,
    DOCKERFILE_PYTHON,
    NUA_BUILDER_TAG,
    NUA_LINUX_BASE,
    NUA_PYTHON_TAG,
    NUA_WHEEL_DIR,
)
from ..docker_utils_build import display_docker_img, docker_build_log_error
from ..state import set_verbose, verbosity

# from shutil import ignore_patterns


app = typer.Typer()

option_verbose = typer.Option(
    0, "--verbose", "-v", help="Show more informations, until -vvv. ", count=True
)


def build_nua_builder():
    print_green(f"*** Generation of the docker image {NUA_BUILDER_TAG} ***")
    build_python_layer()
    build_builder_layer()


def set_temp_build_dir() -> Path:
    build_dir_parent = Path(
        config.get("build", {}).get("build_dir", "/var/tmp")  # noqa S108
    )
    if not build_dir_parent.is_dir():
        error(f"Build directory parent not found: '{build_dir_parent}'")
    build_dir = Path(tempfile.mkdtemp(dir=build_dir_parent))
    return build_dir


def build_python_layer():
    orig_wd = Path.cwd()
    build_dir = set_temp_build_dir()
    copy2(DOCKERFILE_PYTHON, build_dir)
    docker_build_python(build_dir)
    if verbosity(1):
        display_docker_img(NUA_PYTHON_TAG)
    chdir(orig_wd)
    rm_fr(build_dir)


@docker_build_log_error
def docker_build_python(build_dir):
    chdir(build_dir)
    print(f"1/2: Building image {NUA_PYTHON_TAG}")
    if verbosity(1):
        print(f"build directory: {build_dir}")
    app_id = "nua-python"
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_PYTHON).name,
        buildargs={"nua_linux_base": NUA_LINUX_BASE},
        tag=NUA_PYTHON_TAG,
        labels={
            "APP_ID": app_id,
            "NUA_TAG": NUA_PYTHON_TAG,
            "NUA_BUILD_VERSION": nua_version,
        },
        rm=False,
    )


def build_builder_layer():
    orig_wd = Path.cwd()
    build_dir = set_temp_build_dir()
    copy2(DOCKERFILE_BUILDER, build_dir)
    copy_myself(build_dir)
    docker_build_builder(build_dir)
    if verbosity(1):
        display_docker_img(NUA_BUILDER_TAG)
    chdir(orig_wd)
    rm_fr(build_dir)


@docker_build_log_error
def docker_build_builder(build_dir):
    chdir(build_dir)
    app_id = "nua-builder"
    print(f"2/2: Building image {NUA_BUILDER_TAG}")
    if verbosity(1):
        print(f"build directory: {build_dir}")
    client = docker.from_env()
    image, tee = client.images.build(
        path=".",
        dockerfile=Path(DOCKERFILE_BUILDER).name,
        buildargs={"nua_python_tag": NUA_PYTHON_TAG, "nua_version": nua_version},
        tag=NUA_BUILDER_TAG,
        labels={
            "APP_ID": app_id,
            "NUA_TAG": NUA_BUILDER_TAG,
            "NUA_BUILD_VERSION": nua_version,
        },
        rm=False,
    )


# def copy_myself(build_dir):
#     print("Copying nua_build python code")
#     copytree(
#         MYSELF_DIR,
#         build_dir / f"nua_build_{nua_version}",  # fix cache issues
#         ignore=ignore_patterns("*.pyc", "__pycache__", "_build"),
#     )


def copy_myself(build_dir: Path):
    wheel_list = list(NUA_WHEEL_DIR.glob("nua_build*.whl"))
    if not wheel_list:
        raise RuntimeError(
            f"Missing {NUA_WHEEL_DIR} wheel\n"
            "[fixme]: Make new installation of the package with ./build.sh"
        )
    dest = build_dir / "nua_build_whl"
    mkdir_p(dest)
    copy2(wheel_list[-1], dest)


@app.command("build_nua_docker")
def generate_nua_docker_cmd(verbose: int = option_verbose) -> None:
    """build the base Nua docker image."""
    set_verbose(verbose)
    build_nua_builder()
