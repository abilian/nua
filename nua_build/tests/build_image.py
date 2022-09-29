import os
import shlex
import subprocess as sp  # noqa, required.
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from time import perf_counter

import docker
import tomli


def build_test_image(src_dir: Path | str):
    """Build an image and assert success."""
    src_path = Path(src_dir)
    if not src_path.is_dir():
        raise ValueError(f"No such folder: {src_path}")

    actual_path = _apply_makefile(src_path)

    with open(actual_path / "nua-config.toml", mode="rb") as rfile:
        conf = tomli.load(rfile)
    meta = conf["metadata"]
    name = meta["id"]
    if not name.startswith("nua-"):
        name = f"nua-{name}"
    name = f"{name}:{meta['version']}"
    if "release" in meta:
        name = f"{name}-{meta['release']}"
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        print("created temporary directory", tmpdirname)
        _build_test(tmpdirname, actual_path, name)

    _apply_makefile_clean(src_path)


def _apply_makefile(src_path: Path) -> Path:
    if not (src_path / "Makefile").is_file():
        return src_path
    previous_path = Path.cwd()
    os.chdir(src_path)
    result = sp.run(["make", "build"], capture_output=True)
    print(" ========= make build ===========")
    print(result.stdout.decode("utf8"))
    print(" ================================")
    os.chdir(previous_path)
    return src_path / "build_dir"


def _apply_makefile_clean(src_path: Path):
    if not (src_path / "Makefile").is_file():
        return
    previous_path = Path.cwd()
    os.chdir(src_path)
    result = sp.run(["make", "clean"], capture_output=True)
    print(" ========= make clean ===========")
    print(result.stdout.decode("utf8"))
    print(" ================================")
    os.chdir(previous_path)


def _build_test(tmpdirname, src_path, name):
    build_dir = Path(tmpdirname) / "build"
    copytree(src_path, build_dir)
    dock = docker.from_env()
    print("----------------------------------------------")
    print(f"Build {name}")
    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    cmd = shlex.split(f"nua-build {build_dir}")
    t0 = perf_counter()
    result = sp.run(cmd, capture_output=True)
    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print("elapsed (s):", perf_counter() - t0)
    print(" ========= result.stdout ===========")
    print(result.stdout.decode("utf8"))
    print(result.stderr.decode("utf8"))
    print(" ===================================")
    assert result.returncode == 0
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
