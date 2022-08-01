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
from nua_build.archive_search import ArchiveSearch
from nua_build.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG


def test_archive_search():
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
    print("building test image")
    cmd = "nua-build ./nodejs-basic"
    result = sp.run(cmd, shell=True, capture_output=True)  # noqa,we want shell here
    assert result.returncode == 0
    assert dock.images.list(image_target)
    cmd = f"docker save {image_target} -o test.tar"
    sp.run(cmd, shell=True, capture_output=False)  # noqa,we want shell here
    arch_search = ArchiveSearch("test.tar")
    internal_config = arch_search.nua_config_dict()
    assert internal_config["metadata"]["id"] == "nodejs-basic"
    chdir(orig_dir)
    rmtree(tmp)
