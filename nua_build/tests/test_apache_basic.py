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


class TestApacheBasic:
    def test_complete_build_without_cache(self):
        """To be preferably launched with :

        pytest -rP test_apache_basic.py
        """
        host_port = 8081
        image_target = "nua-apache-basic:2.4.52-2"
        ubuntu = "ubuntu:22.04"
        # Warn: using /tmp for tests:
        orig_dir = getcwd()
        # Probable insecure usage of temp file/directory :
        tmp = Path("/tmp") / "tmp_test_apache_basic"  # noqa
        if tmp.exists():
            rmtree(tmp)
        tmp.mkdir()
        copytree(
            Path(__file__).parent / "apache-basic",
            tmp / "apache-basic",
        )
        chdir(tmp)
        print("Testing in:", getcwd())
        dock = docker.from_env()
        for im in (ubuntu, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
            print(f"Show '{im}' in cache:", dock.images.list(im))
        print("Clean cache.")
        dock.images.prune()
        for im in reversed((ubuntu, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target)):
            try:  # noqa : no pb, we do it on our images
                # Use 'contextlib.suppress(docker.errors.ImageNotFound)' :
                dock.images.remove(im, force=True, noprune=False)
            except docker.errors.ImageNotFound:
                pass
            assert not dock.images.list(im)
        # DTZ005 The use of `datetime.datetime.now()` without `tz` argument is
        # not allowed : well, by default it uses localtime.
        print("Time now:", datetime.now(timezone.utc).isoformat(" "))
        print(f"Build {image_target} (no images in cache) with command:")
        cmd = "nua-build ./apache-basic"
        print(f"'{cmd}'")
        t0 = perf_counter()
        result = sp.run(cmd, shell=True, capture_output=True)  # noqa, we want shell

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
        container = dock.containers.run(
            image_target,
            detach=True,
            ports={"80/tcp": host_port},
        )
        sleep(2)
        cmd = f"curl http://127.0.0.1:{host_port}"
        # S603 subprocess call - check for execution of untrusted input.: wrong
        curl_result = sp.run(cmd, shell=True, capture_output=True)  # noqa
        assert curl_result.returncode == 0
        test_string = f"<h1>Nua test {nua_version}</h1>"
        assert test_string in curl_result.stdout.decode("utf8")
        print(test_string)
        container.kill()
        chdir(orig_dir)
        rmtree(tmp)

    def test_complete_build_with_cache(self):
        """To be preferably launched with :

        pytest -rP test_apache_basic.py
        """
        host_port = 8081
        image_target = "nua-apache-basic:2.4.52-2"
        ubuntu = "ubuntu:22.04"
        # Warn: using /tmp for tests:
        orig_dir = getcwd()
        # Probable insecure usage of temp file/directory :
        tmp = Path("/tmp") / "tmp_test_apache_basic"  # noqa
        if tmp.exists():
            rmtree(tmp)
        tmp.mkdir()
        copytree(
            Path(__file__).parent / "apache-basic",
            tmp / "apache-basic",
        )
        chdir(tmp)
        print("Testing in:", getcwd())
        dock = docker.from_env()
        for im in (ubuntu, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
            print(f"Show '{im}' in cache:", dock.images.list(im))
        print("Time now:", datetime.now(timezone.utc).isoformat(" "))
        print(f"Build {image_target} (expecting cache) with nua command line:")
        cmd = "nua-build ./apache-basic"
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
        container = dock.containers.run(
            image_target,
            detach=True,
            ports={"80/tcp": host_port},
        )
        sleep(2)
        cmd = f"curl http://127.0.0.1:{host_port}"
        # S603 subprocess call - check for execution of untrusted input.: wrong
        curl_result = sp.run(cmd, shell=True, capture_output=True)  # noqa
        assert curl_result.returncode == 0
        test_string = f"<h1>Nua test {nua_version}</h1>"
        assert test_string in curl_result.stdout.decode("utf8")
        print(test_string)
        container.kill()
        chdir(orig_dir)
        rmtree(tmp)
