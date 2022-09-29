import shlex
import subprocess as sp  # noqa, required.
import tempfile
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from time import perf_counter, sleep

import docker

from nua_build import __version__ as nua_version
from nua_build.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG

UBUNTU = "ubuntu:jammy-20220801"


class TestApacheBasic:
    def test_complete_build_without_cache(self):
        """To be preferably launched with :

        pytest -rP test_apache_basic.py
        """
        host_port = 8081
        src_path = Path(__file__).parent / "apache_basic"
        image_target = "nua-apache-basic:2.4.52-2"
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
            build_dir = Path(tmpdirname) / "build"
            copytree(src_path, build_dir)
            dock = docker.from_env()

            for image in (UBUNTU, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
                print(f"Show '{image}' in cache:", dock.images.list(image))

            print("Clean cache.")
            dock.images.prune()

            for image in reversed(
                (UBUNTU, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target)
            ):
                with suppress(docker.errors.ImageNotFound):
                    dock.images.remove(image, force=True, noprune=False)
                assert not dock.images.list(image)

            # DTZ005 The use of `datetime.datetime.now()` without `tz` argument is
            # not allowed : well, by default it uses localtime.
            print("Time now:", datetime.now(timezone.utc).isoformat(" "))
            print(f"Build {image_target} (no images in cache) with command:")
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
        container = dock.containers.run(
            image_target,
            detach=True,
            ports={"80/tcp": host_port},
        )
        sleep(2)
        cmd = shlex.split(f"curl http://127.0.0.1:{host_port}")
        # S603 subprocess call - check for execution of untrusted input.: wrong
        curl_result = sp.run(cmd, capture_output=True)
        assert curl_result.returncode == 0
        test_string = f"<h1>Nua test {nua_version}</h1>"
        assert test_string in curl_result.stdout.decode("utf8")
        print(test_string)
        container.kill()

    def test_complete_build_with_cache(self):
        """To be preferably launched with :

        pytest -rP test_apache_basic.py
        """
        host_port = 8081
        src_path = Path(__file__).parent / "apache_basic"
        image_target = "nua-apache-basic:2.4.52-2"
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
            build_dir = Path(tmpdirname) / "build"
            copytree(src_path, build_dir)
            dock = docker.from_env()

            for image in (UBUNTU, NUA_PYTHON_TAG, NUA_BUILDER_TAG, image_target):
                print(f"Show '{image}' in cache:", dock.images.list(image))

            print("Time now:", datetime.now(timezone.utc).isoformat(" "))
            print(f"Build {image_target} (no images in cache) with command:")
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
        container = dock.containers.run(
            image_target,
            detach=True,
            ports={"80/tcp": host_port},
        )
        sleep(2)
        cmd = shlex.split(f"curl http://127.0.0.1:{host_port}")
        # S603 subprocess call - check for execution of untrusted input.: wrong
        curl_result = sp.run(cmd, capture_output=True)
        assert curl_result.returncode == 0
        test_string = f"<h1>Nua test {nua_version}</h1>"
        assert test_string in curl_result.stdout.decode("utf8")
        print(test_string)
        container.kill()
