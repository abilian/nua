import subprocess as sp
import tempfile
from pathlib import Path
from shutil import copytree
from time import perf_counter

import docker

from nua.build.builders import get_builder
from nua.lib.backports import chdir
from nua.lib.nua_config import NuaConfig


def build_test_image(src_dir: Path | str):
    """Build an image and assert success."""
    src_path = Path(src_dir)
    assert src_path.is_dir()

    with chdir(src_path):
        conf = NuaConfig()
        name = conf.nua_tag
        if Path("Makefile").is_file():
            # assert False, "Do we still have this case ?"
            _makefile_build_test(name)
        else:
            _build_test_tmpdir(name)


def _makefile_build_test(name):
    _run_make("build")
    with chdir("build_dir"):
        _build_test_tmpdir(name)
    _run_make("clean")


def _build_test_tmpdir(name: str):
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        print("Building in temporary directory", tmpdirname)
        _build_test(tmpdirname, name)


def _run_make(target: str):
    print(f" ========= make {target} ===========")
    result = sp.run(["make", target], capture_output=True)
    print(result.stdout.decode("utf8"))
    print(" ================================")


def _build_test(tmpdirname: str, name: str, expect_failure: bool = False):
    build_dir = Path(tmpdirname) / "build"
    copytree(".", build_dir)
    docker_client = docker.from_env()

    print("----------------------------------------------")
    print(f"Build {name}")

    t0 = perf_counter()

    builder = get_builder(save_image=False)
    builder.run()

    print("elapsed (s):", perf_counter() - t0)

    assert docker_client.images.list(name)

    print("In the container:")
    # clean previous run if any
    for previous in docker_client.containers.list(filters={"ancestor": name}):
        previous.kill()
    kwargs = {
        "remove": True,
        "entrypoint": [],
    }
    print(
        docker_client.containers.run(
            name, command="ls -l /nua/metadata/", **kwargs
        ).decode("utf8")
    )
