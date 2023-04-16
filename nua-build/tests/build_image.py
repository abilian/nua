import subprocess as sp
import tempfile
from pathlib import Path
from shutil import copytree
from time import perf_counter

import docker
from nua.agent.nua_config import NuaConfig
from nua.lib.backports import chdir
from typer.testing import CliRunner

from nua.build.builder import get_builder

runner = CliRunner(mix_stderr=False)


def build_test_image(src_dir: Path | str):
    """Build an image and assert success."""
    src_path = Path(src_dir)
    assert src_path.is_dir()

    with chdir(src_path):
        conf = NuaConfig()
        name = conf.nua_tag
        if Path("Makefile").is_file():
            _makefile_build_test(name)
        else:
            _build_test_tmpdir(name)


def build_test_image_expect_fail(src_dir: Path | str):
    """Build an image and assert failure."""
    src_path = Path(src_dir)
    assert src_path.is_dir()

    with chdir(src_path):
        conf = NuaConfig()
        name = conf.nua_tag
        if Path("Makefile").is_file():
            _makefile_build_test_failure(name)
        else:
            _build_test_tmpdir_failure(name)


def _makefile_build_test(name):
    _run_make("build")
    with chdir("build_dir"):
        _build_test_tmpdir(name)
    _run_make("clean")


def _makefile_build_test_failure(name):
    _run_make("build")
    with chdir("build_dir"):
        _build_test_tmpdir_failure(name)
    _run_make("clean")


def _build_test_tmpdir(name: str):
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        print("Building in temporary directory", tmpdirname)
        _build_test(tmpdirname, name)


def _build_test_tmpdir_failure(name: str):
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        print("Building in temporary directory", tmpdirname)
        _build_test(tmpdirname, name, expect_failure=True)


def _run_make(target: str):
    print(f" ========= make {target} ===========")
    result = sp.run(["make", target], capture_output=True)
    print(result.stdout.decode("utf8"))
    print(" ================================")


def _build_test(tmpdirname: str, name: str, expect_failure: bool = False):
    build_dir = Path(tmpdirname) / "build"
    # print("in _build_test()")
    # print(f"cwd: {Path.cwd()}")
    # print(os.listdir("."))
    copytree(".", build_dir)
    dock = docker.from_env()

    print("----------------------------------------------")
    print(f"Build {name}")

    t0 = perf_counter()

    builder = get_builder()
    builder.run()
    # result = runner.invoke(app, ["-vv", str(build_dir)])

    print("elapsed (s):", perf_counter() - t0)

    # print(" ========= result.stdout ===========")
    # print(result.stdout)
    # print(result.stderr)
    # print(" ===================================")
    #
    # if expect_failure:
    #     assert result.exit_code != 0
    #     return
    #
    # assert result.exit_code == 0

    assert dock.images.list(name)

    print("In the container:")
    # clean previous run if any
    for previous in dock.containers.list(filters={"ancestor": name}):
        previous.kill()
    kwargs = {
        "remove": True,
        "entrypoint": [],
    }
    print(
        dock.containers.run(name, command="ls -l /nua/metadata/", **kwargs).decode(
            "utf8"
        )
    )
