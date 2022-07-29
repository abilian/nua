import os
import subprocess as sp  # noqa, required.
from datetime import datetime, timezone
from os import chdir, getcwd
from pathlib import Path
from shutil import copytree, rmtree
from time import perf_counter, sleep

import docker
import pytest

from nua_build import __version__ as nua_version
from nua_build.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG


def test_complete_build_with_cache():
    """To be preferably launched with :

    pytest -rP test_nodejs_basic.py
    """
    image_target = "nua-nodejs-basic:1.6-1"
    ubuntu = "ubuntu:22.04"
    # Warn: using /tmp for tests:
    orig_dir = getcwd()
    # Probable insecure usage of temp file/directory :
    tmp = Path("/tmp") / "tmp_test_nodejs_basic"  # noqa
    if tmp.exists():
        rmtree(tmp)
    tmp.mkdir()
    copytree(
        Path(__file__).parent / "nodejs-basic",
        tmp / "nodejs-basic",
    )
    chdir(tmp)
    print("Testing in:", getcwd())
    dock = docker.from_env()
    for im in (ubuntu, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
        print(f"Show '{im}' in cache:", dock.images.list(im))
    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print(f"Build {image_target} (expecting cache) with nua command line:")
    cmd = "nua-build ./nodejs-basic"
    print(f"'{cmd}'")
    t0 = perf_counter()
    result = sp.run(cmd, shell=True, capture_output=True)  # noqa,we want shell here

    print("Time now:", datetime.now(timezone.utc).isoformat(" "))
    print("elapsed (s):", perf_counter() - t0)
    print(" ========= result.stdout ===========")
    print(result.stdout.decode("utf8"))
    print(" ===================================")
    assert result.returncode == 0
    assert dock.images.list(im)
    print("Testing the container:")
    # clean previous run if any
    for previous in dock.containers.list(filters={"ancestor": image_target}):
        previous.kill()
    dock.containers.run(image_target, command="/usr/bin/node --help")
    sleep(2)
    chdir(orig_dir)
    rmtree(tmp)
