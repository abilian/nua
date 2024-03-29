import shlex
import subprocess as sp
import tempfile
from pathlib import Path
from shutil import copytree
from unittest import skip

from cleez.testing import CliRunner
from docker import DockerClient
from nua.lib.archive_search import ArchiveSearch
from nua.lib.nua_config import NuaConfig

from nua.build.main import app as nua_build

from .common import get_apps_root_dir

runner = CliRunner()


def test_archive_search():
    app_id = "flask-one-wheel"
    src_path = get_apps_root_dir("sample-apps") / app_id.replace("-", "_")
    image_target = image_name(src_path)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
        _build_test_search(tmpdirname, src_path, image_target, app_id)


def _build_test_search(tmpdirname, src_path, image_target, app_id):
    build_dir = Path(tmpdirname) / "build"
    copytree(src_path, build_dir)
    docker = DockerClient.from_env()

    # build the app "flask-one-wheel"
    build_app(build_dir)

    print("image:", image_target)
    print(docker.images.list(image_target))
    assert docker.images.list(image_target)

    # actual test of the ArchiveSearch() class
    archive = Path(tmpdirname) / "test.tar"
    cmd = shlex.split(f"docker save {image_target} -o {archive}")
    sp.run(cmd)  # noqa S603
    arch_search = ArchiveSearch(archive)
    internal_config = arch_search.get_nua_config_dict()
    assert internal_config["metadata"]["id"] == app_id


@skip("FIXME")
def build_app(build_dir: Path) -> None:
    """Quick build the application with nua-build."""
    result = runner.invoke(nua_build, ["-v", str(build_dir)])
    print(result.stdout)
    print(result.stderr)
    assert result.exit_code == 0


def image_name(src_path: Path) -> str:
    """Open nua-config file and return the expected image target name."""
    config = NuaConfig(src_path)
    return config.nua_tag
