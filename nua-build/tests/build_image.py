import os
import subprocess as sp
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from time import perf_counter

import docker
import tomli
from typer.testing import CliRunner

from nua.build.backports import chdir
from nua.build.main import app

runner = CliRunner(mix_stderr=False)


def build_test_image(src_dir: Path | str):
    """Build an image and assert success."""
    src_path = Path(src_dir)
    assert src_path.is_dir()

    with chdir(src_path):
        with open("nua-config.toml", mode="rb") as rfile:
            conf = tomli.load(rfile)

        name = _make_image_name(conf)

        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
            print("Building in temporary directory", tmpdirname)
            _build_test(tmpdirname, name)

        _run_make("clean")


def _make_image_name(conf: dict) -> str:
    meta = conf["metadata"]
    name = meta["id"]
    if not name.startswith("nua-"):
        name = f"nua-{name}"
    name = f"{name}:{meta['version']}"
    if "release" in meta:
        name = f"{name}-{meta['release']}"
    return name


def _run_make(target: str) -> None:
    if not Path("Makefile").is_file():
        return

    print(" ========= make build ===========")
    result = sp.run(["make", target], capture_output=True)
    print(result.stdout.decode("utf8"))
    print(" ================================")


def _build_test(tmpdirname: str, name: str):
    build_dir = Path(tmpdirname) / "build"
    copytree(".", build_dir)
    dock = docker.from_env()
    print("----------------------------------------------")
    print(f"Build {name}")
    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print(os.environ)
    t0 = perf_counter()
    result = runner.invoke(app, [str(build_dir)])
    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print("elapsed (s):", perf_counter() - t0)
    print(" ========= result.stdout ===========")
    print(result.stdout)
    print(result.stderr)
    print(" ===================================")
    assert result.exit_code == 0
    assert dock.images.list(name)

    print("In the container:")
    # clean previous run if any
    for previous in dock.containers.list(filters={"ancestor": name}):
        previous.kill()
    print(
        dock.containers.run(
            name, command="head -12 /nua/metadata/nua-config.toml"
        ).decode("utf8")
    )
