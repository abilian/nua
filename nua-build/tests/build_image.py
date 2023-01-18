import subprocess as sp
import tempfile
from pathlib import Path
from shutil import copytree
from time import perf_counter

import docker
from nua.lib.backports import chdir
from nua.runtime.nua_config import NuaConfig
from typer.testing import CliRunner

from nua.build.main import app

runner = CliRunner(mix_stderr=False)


def build_test_image(src_dir: Path | str):
    """Build an image and assert success."""
    src_path = Path(src_dir)
    assert src_path.is_dir()

    with chdir(src_path):
        conf = NuaConfig(".").as_dict()
        name = _make_image_name(conf)
        if Path("Makefile").is_file():
            _makefile_build_test(name)
        else:
            _build_test_tmpdir(name)


def build_test_image_expect_fail(src_dir: Path | str):
    """Build an image and assert failure."""
    src_path = Path(src_dir)
    assert src_path.is_dir()

    with chdir(src_path):
        conf = NuaConfig(".").as_dict()
        name = _make_image_name(conf)
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


def _make_image_name(conf: dict) -> str:
    meta = conf["metadata"]
    name = meta["id"]
    if not name.startswith("nua-"):
        name = f"nua-{name}"
    name = f"{name}:{meta['version']}"
    if "release" in meta:
        name = f"{name}-{meta['release']}"
    return name


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
    # print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    # print(os.environ)
    t0 = perf_counter()
    result = runner.invoke(app, ["-vv", str(build_dir)])
    # print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print("elapsed (s):", perf_counter() - t0)
    print(" ========= result.stdout ===========")
    print(result.stdout)
    print(result.stderr)
    print(" ===================================")

    if expect_failure:
        assert result.exit_code != 0
        return

    assert result.exit_code == 0
    assert dock.images.list(name)

    print("In the container:")
    # clean previous run if any
    for previous in dock.containers.list(filters={"ancestor": name}):
        previous.kill()
    print(dock.containers.run(name, command="ls -l /nua/metadata/").decode("utf8"))
