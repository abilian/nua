import shlex
import subprocess as sp  # noqa, required.
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from time import perf_counter, sleep

import docker

from nua_build.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG

UBUNTU = "ubuntu:jammy-20220801"


def test_complete_build_with_cache():
    """To be preferably launched with :

    pytest -rP test_nodejs_basic.py
    """
    image_target = "nua-nodejs-basic:1.6-1"
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        dest = Path(tmp) / "nodejs-basic"
        copytree(Path(__file__).parent / "nodejs-basic", dest)
        dock = docker.from_env()
        for im in (UBUNTU, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
            print(f"Show '{im}' in cache:", dock.images.list(im))
        print("Time now:", datetime.now(timezone.utc).isoformat(" "))
        print(f"Build {image_target} (expecting cache) with nua command line:")
        cmd = shlex.split(f"nua-build {dest}")
        print(f"'{cmd}'")
        t0 = perf_counter()
        result = sp.run(cmd, capture_output=True)  # noqa,we want shell here
        print("Time now:", datetime.now(timezone.utc).isoformat(" "))
        print("elapsed (s):", perf_counter() - t0)
        print(" ========= result.stdout ===========")
        print(result.stdout.decode("utf8"))
        print(result.stderr.decode("utf8"))
        print(" ===================================")
        assert result.returncode == 0
        assert dock.images.list(im)
        print("Testing the container:")
        # clean previous run if any
        for previous in dock.containers.list(filters={"ancestor": image_target}):
            previous.kill()
        dock.containers.run(image_target, command="/usr/bin/node --help")
        sleep(2)
