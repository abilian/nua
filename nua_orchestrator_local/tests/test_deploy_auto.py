import os
import tempfile
from pathlib import Path

import pytest
import requests
import tomli
from typer.testing import CliRunner

from nua_orchestrator_local.main import app

from .replace_domain import replace_file

runner = CliRunner()

DEPLOY_CONFIGS = Path(__file__).parent / "deploy_configs"
DEPLOY_AUTO_FILES = sorted((Path(__file__).parent / "deploy_auto_check").glob("*.toml"))

os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


def _make_check_test(test: dict):
    url = test.get("url")
    if not url:
        return
    if os.environ.get("NUA_CERTBOT_STRATEGY").lower() == "none":
        url = url.replace("https://", "http://")
    else:
        url = url.replace("http://", "https://")
    print("testing: ", url)
    response = requests.get(url)
    expect_status = test.get("expect_status")
    if expect_status is not None:
        assert response.status_code == expect_status
    expect_str = test.get("expect_str")
    if expect_str:
        assert expect_str in response.content.decode("utf8")


def _check_sites(toml):
    with open(toml, "rb") as rfile:
        content = tomli.load(rfile)
    for site in content["site"]:
        if "test" not in site:
            continue
        for test in site["test"]:
            _make_check_test(test)


@pytest.mark.parametrize("deploy_file", DEPLOY_AUTO_FILES)
def test_deploy_sites(deploy_file):
    print("\n" + "-" * 40)
    print(deploy_file)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        new_file = replace_file(deploy_file, tmp_dir)

        result = runner.invoke(app, f"deploy -vv {new_file}")
        print(result.stdout)

        assert result.exit_code == 0
        assert "Installing App" in result.stdout
        assert "deployed as" in result.stdout

        _check_sites(new_file)
