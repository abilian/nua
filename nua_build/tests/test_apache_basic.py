import subprocess as sp
from datetime import datetime
from os import chdir, getcwd
from pathlib import Path
from shutil import copytree, rmtree
from time import perf_counter, sleep

import docker

from nua_build import __version__ as nua_version
from nua_build.constants import NUA_BASE_TAG, NUA_MIN_TAG


def test_complete_build_without_cache():
    """To be preferably launched with :
    pytest -rP test_apache_basic.py
    """
    host_port = 8081
    image_target = "nua-apache-basic:2.4.52-2"
    ubuntu = "ubuntu:22.04"
    # Warn: using /tmp for tests:
    orig_dir = getcwd()
    tmp = Path("/tmp") / "tmp_test_apache_basic"
    if tmp.exists():
        rmtree(tmp)
    tmp.mkdir()
    copytree(
        Path(__file__).parent / "test_apache_basic" / "apache-basic",
        tmp / "apache-basic",
    )
    chdir(tmp)
    print("Testing in:", getcwd())

    dock = docker.from_env()
    for im in (ubuntu, NUA_MIN_TAG, NUA_BASE_TAG, image_target):
        print(f"Show '{im}' in cache:", dock.images.list(im))
    print("Clean cache.")
    dock.images.prune()
    for im in reversed((ubuntu, NUA_MIN_TAG, NUA_BASE_TAG, image_target)):
        try:
            dock.images.remove(im, force=True, noprune=False)
        except docker.errors.ImageNotFound:
            pass
        assert not dock.images.list(im)

    print("Time now:", datetime.now().isoformat(" "))
    print(f"Build {image_target} (no images in cache) with command:")
    cmd = "nuad build ./apache-basic"
    print(f"'{cmd}'")

    t0 = perf_counter()
    result = sp.run(cmd, shell=True, capture_output=True)
    print("Time now:", datetime.now().isoformat(" "))
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
    curl_result = sp.run(cmd, shell=True, capture_output=True)
    assert curl_result.returncode == 0
    test_string = f"<h1>Nua test {nua_version}</h1>"
    assert test_string in curl_result.stdout.decode("utf8")
    print(test_string)
    container.kill()
    chdir(orig_dir)
    rmtree(tmp)


def test_complete_build_with_cache():
    """To be preferably launched with :
    pytest -rP test_apache_basic.py
    """
    host_port = 8081
    image_target = "nua-apache-basic:2.4.52-2"
    ubuntu = "ubuntu:22.04"
    # Warn: using /tmp for tests:
    orig_dir = getcwd()
    tmp = Path("/tmp") / "tmp_test_apache_basic"
    if tmp.exists():
        rmtree(tmp)
    tmp.mkdir()
    copytree(
        Path(__file__).parent / "test_apache_basic" / "apache-basic",
        tmp / "apache-basic",
    )
    chdir(tmp)
    print("Testing in:", getcwd())

    dock = docker.from_env()
    for im in (ubuntu, NUA_MIN_TAG, NUA_BASE_TAG, image_target):
        print(f"Show '{im}' in cache:", dock.images.list(im))

    print("Time now:", datetime.now().isoformat(" "))
    print(f"Build {image_target} (expecting cache) with nua command line:")
    cmd = "nuad build ./apache-basic"
    print(f"'{cmd}'")

    t0 = perf_counter()
    result = sp.run(cmd, shell=True, capture_output=True)
    print("Time now:", datetime.now().isoformat(" "))
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
    curl_result = sp.run(cmd, shell=True, capture_output=True)
    assert curl_result.returncode == 0
    test_string = f"<h1>Nua test {nua_version}</h1>"
    assert test_string in curl_result.stdout.decode("utf8")
    print(test_string)
    container.kill()
    chdir(orig_dir)
    rmtree(tmp)
