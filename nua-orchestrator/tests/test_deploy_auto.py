import os
import shlex
import socket
import subprocess as sp
import tempfile
from pathlib import Path

import pytest
import requests
import tomli
from typer.testing import CliRunner

from nua.orchestrator.cli.main import app

runner = CliRunner()

this_dir = Path(__file__).parent
DEPLOY_CONFIGS = this_dir / "deploy_configs"
DEPLOY_AUTO_FILES = [str(p) for p in sorted((this_dir / "configs_ok").glob("*.toml"))]

os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


@pytest.mark.parametrize("deploy_file", DEPLOY_AUTO_FILES)
def test_deploy_sites(deploy_file: str):
    print("\n" + "-" * 40)
    print(f"test config: {deploy_file}")

    domain_name = os.environ.get("NUA_DOMAIN_NAME", "")
    if not domain_name:
        domain_name = socket.gethostname()

    with tempfile.NamedTemporaryFile("w", suffix=".toml") as new_file:
        with open(deploy_file) as old_file:
            data = old_file.read()
            data = data.replace("example.com", domain_name)
            new_file.write(data)
            new_file.flush()

        cmd = f"deploy -vv {new_file.name}"
        result = runner.invoke(app, cmd)
        print(result.stdout)

        assert result.exit_code == 0
        assert "Installing App" in result.stdout
        assert "deployed as" in result.stdout

        _check_sites(Path(new_file.name))


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


def _check_sites(deploy_file: Path):
    content = tomli.loads(deploy_file.read_text(encoding="utf8"))
    for site in content["site"]:
        if "test" not in site:
            continue
        for test in site["test"]:
            _make_check_test(test)
