import shlex
import subprocess as sp  # noqa, required.
import tempfile
from pathlib import Path
from shutil import copytree

from docker import DockerClient

from nua.build.archive_search import ArchiveSearch
from .common import get_apps_root_dir


def test_archive_search():
    app_id = "flask-one-wheel"
    image_target = "nua-flask-one-wheel:1.2-1"
    src_path = get_apps_root_dir("sample-apps") / app_id.replace("-", "_")

    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        _build_test_search(tmpdirname, src_path, image_target, app_id)


def _build_test_search(tmpdirname, src_path, image_target, app_id):
    build_dir = Path(tmpdirname) / "build"
    copytree(src_path, build_dir)
    docker = DockerClient.from_env()

    cmd = shlex.split(f"nua-build {build_dir}")
    result = sp.run(cmd, capture_output=True)
    assert result.returncode == 0
    assert docker.images.list(image_target)

    archive = Path(tmpdirname) / "test.tar"
    cmd = shlex.split(f"docker save {image_target} -o {archive}")
    sp.run(cmd)
    arch_search = ArchiveSearch(archive)
    internal_config = arch_search.nua_config_dict()
    assert internal_config["metadata"]["id"] == app_id
