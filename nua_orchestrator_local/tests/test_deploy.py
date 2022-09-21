from pathlib import Path

import requests
import tomli
from typer.testing import CliRunner

from nua_orchestrator_local import __version__
from nua_orchestrator_local.main import app

runner = CliRunner()

CONFIGS = Path(__file__).parent / "deploy_configs"


def test_no_exist():
    toml = CONFIGS / "no_such_file.toml"
    result = runner.invoke(app, f"deploy {toml}")

    assert "No image found" in result.stdout
    assert result.exit_code == 1


def test_no_image():
    toml = CONFIGS / "no_image.toml"
    result = runner.invoke(app, f"deploy {toml}")

    assert ("No image found" in result.stdout) or (
        "Something went wrong" in result.stdout
    )
    assert result.exit_code == 1


def _make_check_test(test: dict):
    url = test.get("url")
    if not url:
        return
    print("testing: ", url)
    response = requests.get(url)
    expect_status = test.get("expect_status")
    if expect_status is not None:
        assert response.status_code == expect_status
    expect_str = test["expect_str"]
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


def _check_deploy(toml: dict):
    result = runner.invoke(app, f"deploy {toml}")
    print(result.stdout)

    assert result.exit_code == 0
    assert "Installing App" in result.stdout
    assert "deployed as" in result.stdout

    _check_sites(toml)


def test_flask_one():
    _check_deploy(CONFIGS / "flask_one.toml")
