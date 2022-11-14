import shlex
import subprocess as sp  # noqa, required.
import tempfile
from pathlib import Path
from shutil import copytree

import docker

from nua.build.archive_search import ArchiveSearch


def test_archive_search():
    src_path = Path(__file__).parent / "apps" / "nodejs_install"
    image_target = "nua-nodejs-test:1.0-1"
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        _build_test_search(tmpdirname, src_path, image_target)


def _build_test_search(tmpdirname, src_path, image_target):
    build_dir = Path(tmpdirname) / "build"
    copytree(src_path, build_dir)
    dock = docker.from_env()

    cmd = shlex.split(f"nua-build {build_dir}")
    result = sp.run(cmd, capture_output=True)
    assert result.returncode == 0
    assert dock.images.list(image_target)

    archive = Path(tmpdirname) / "test.tar"
    cmd = shlex.split(f"docker save {image_target} -o {archive}")
    sp.run(cmd)
    arch_search = ArchiveSearch(archive)
    internal_config = arch_search.nua_config_dict()
    assert internal_config["metadata"]["id"] == "nodejs-test"
