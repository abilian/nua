import shlex
import subprocess as sp  # noqa, required.
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from time import perf_counter

import docker

from nua_build.constants import NUA_BUILDER_TAG, NUA_LINUX_BASE, NUA_PYTHON_TAG


def test_complete_build_with_cache():
    """To be preferably launched with :

    pytest -rP test_nodejs_install.py
    """
    src_path = Path(__file__).parent / "apps" / "nodejs_install"
    image_target = "nua-nodejs-test:1.0-1"
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        _build_test_cache(tmpdirname, src_path, image_target)


def _build_test_cache(tmpdirname, src_path, image_target):
    build_dir = Path(tmpdirname) / "build"
    copytree(src_path, build_dir)
    dock = docker.from_env()

    for name in (NUA_LINUX_BASE, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
        print(f"Show '{name}' in cache:", dock.images.list(name))

    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print(f"Build {image_target} (expecting cache) with nua command line:")
    cmd = shlex.split(f"nua-build {build_dir}")
    print(f"'{cmd}'")
    t0 = perf_counter()
    result = sp.run(cmd, capture_output=True)
    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print("elapsed (s):", perf_counter() - t0)
    print(" ========= result.stdout ===========")
    print(result.stdout.decode("utf8"))
    print(result.stderr.decode("utf8"))
    print(" ===================================")
    assert result.returncode == 0
    assert dock.images.list(image_target)
    print("Testing the container:")
    # clean previous run if any
    for previous in dock.containers.list(filters={"ancestor": image_target}):
        previous.kill()
    dock.containers.run(image_target, command="/usr/bin/node --help")
