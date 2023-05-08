import os
import shlex
import socket
import subprocess as sp
import tempfile
from pathlib import Path
import shutil
import requests
from typer.testing import CliRunner

from nua.orchestrator.cli.main import app
from nua.orchestrator.utils import parse_any_format
from nua.lib.exec import is_current_user
from subprocess import run

runner = CliRunner(mix_stderr=False)


def deploy_one_site(deploy_file: str):
    print("\n" + "-" * 40)
    print(f"test config: {deploy_file}")
    domain_name = os.environ.get("NUA_DOMAIN_NAME", "")
    if not domain_name:
        domain_name = socket.gethostname()
    print(f"replacing 'example.com' by: '{domain_name}'")
    orchestrator = shutil.which("nua-orchestrator")
    assert orchestrator is not None
    suffix = Path(deploy_file).suffix

    with tempfile.NamedTemporaryFile("w", suffix=suffix) as new_file:
        with open(deploy_file) as old_file:
            data = old_file.read()
            data = data.replace("example.com", domain_name)
            new_file.write(data)
            new_file.flush()

        # shutil

        # deploy_merge_nua_app

        if os.getuid() == 0 or is_current_user("nua"):
            cmd = f"{orchestrator} deploy -vv {new_file.name}"
        else:
            os.chmod(new_file.name, 0o644)
            cmd = f"sudo {orchestrator} deploy -vv {new_file.name}"

        result = run(
            cmd,
            shell=True,  # noqa: S602
            timeout=600,
            executable="/bin/bash",
            text=True,
            capture_output=True,
        )

        if result.stdout:
            print(" ========= result.stdout ===========")
            print(result.stdout)
        if result.stderr:
            print(" ========= result.stderr ===========")
            print(result.stderr)

        assert result.returncode == 0
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
    response = requests.get(url, timeout=60)
    _apply_check_suite(test, response)


def _check_sites(deploy_file: Path):
    content = parse_any_format(deploy_file)
    for site in content["site"]:
        if "test" not in site:
            continue
        for test in site["test"]:
            _make_check_test(test)
