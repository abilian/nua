import os
import shlex
import subprocess as sp
import tempfile
from pathlib import Path

import pytest
import requests
import tomli
from typer.testing import CliRunner

from nua.orchestrator.main import app
from nua.orchestrator.scripts.test_replace_domain import replace_file

runner = CliRunner()

DEPLOY_CONFIGS = Path(__file__).parent / "deploy_configs"
DEPLOY_AUTO_FILES = sorted((Path(__file__).parent / "deploy_auto_check").glob("*.toml"))
REPLACE_DOMAIN = Path(__file__).parent / "REPLACE_DOMAIN"

os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


def _assert_expect_status(expected: int | str | None, response: requests.Response):
    if expected is not None:
        assert response.status_code == int(expected)


def _assert_expect_not_status(expected: int | str | None, response: requests.Response):
    if expected is not None:
        assert response.status_code != int(expected)


def _assert_expect_str(expected: str | None, response: requests.Response):
    if expected:
        assert str(expected) in response.content.decode("utf8")


def _assert_expect_not_str(expected: str | None, response: requests.Response):
    if expected:
        assert str(expected) not in response.content.decode("utf8")


def _assert_expect_host_volume(expected: str | None, response: requests.Response):
    if expected:
        if os.getuid() == 0:
            # easy if root:
            path = Path("/var/lib/docker/volumes") / expected
            assert path.exists()
        else:
            result = sp.run(
                shlex.split("docker volume ls -f 'driver=local'"), capture_output=True
            )
            words = result.stdout.decode("utf8").split()
            assert expected in words


def _assert_expect_not_host_volume(expected: str | None, response: requests.Response):
    if expected:
        if os.getuid() == 0:
            path = Path("/var/lib/docker/volumes") / expected
            assert not path.exists()
        else:
            result = sp.run(
                shlex.split("docker volume ls -f 'driver=local'"), capture_output=True
            )
            words = result.stdout.decode("utf8").split()
            assert expected not in words


def _assert_expect_host_dir(expected: str | None, response: requests.Response):
    """Test local host path."""
    if expected:
        path = Path(expected)
        assert path.exists()


EXPECT_FCT = {
    "expect_status": _assert_expect_status,
    "expect_not_status": _assert_expect_not_status,
    "expect_str": _assert_expect_str,
    "expect_not_str": _assert_expect_not_str,
    "expect_host_volume": _assert_expect_host_volume,
    "expect_not_host_volume": _assert_expect_not_host_volume,
    "expect_host_dir": _assert_expect_host_dir,
}


def _apply_check_suite(test: dict, response: requests.Response):
    for key, value in test.items():
        if key not in EXPECT_FCT or value is None:
            continue
        expect_fct = EXPECT_FCT[key]
        expect_fct(value, response)


def _make_check_test(test: dict):
    url = test.get("url")
    if not url:
        return
    # FIXME: configuration via env var should not be directly exposed
    if os.environ.get("NUA_CERTBOT_STRATEGY", "none").lower() == "none":
        url = url.replace("https://", "http://")
    else:
        url = url.replace("http://", "https://")
    print("testing: ", url)
    response = requests.get(url)
    _apply_check_suite(test, response)


def _check_sites(toml: Path):
    content = tomli.loads(toml.read_text(encoding="utf8"))
    for site in content["site"]:
        if "test" not in site:
            continue
        for test in site["test"]:
            _make_check_test(test)


@pytest.mark.parametrize("deploy_file", DEPLOY_AUTO_FILES)
def test_deploy_sites(deploy_file: Path):
    print("\n" + "-" * 40)
    print(f"test config: {deploy_file.name}")
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        new_file = replace_file(REPLACE_DOMAIN, deploy_file, tmp_dir)

        result = runner.invoke(app, f"deploy -vv {new_file}")
        print(result.stdout)

        assert result.exit_code == 0
        assert "Installing App" in result.stdout
        assert "deployed as" in result.stdout

        _check_sites(new_file)
