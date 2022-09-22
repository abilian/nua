import os
from pathlib import Path

import pytest
import requests
import tomli
from typer.testing import CliRunner

from nua_orchestrator_local import __version__
from nua_orchestrator_local.main import app

runner = CliRunner()

DEPLOY_CONFIGS = Path(__file__).parent / "deploy_configs"
DEPLOY_AUTO_FILES = (Path(__file__).parent / "deploy_auto_check").glob("*.toml")

os.environ["CERTBOT_TEST"] = "1"
os.environ["CERTBOT_VERBOSE"] = "1"


def test_no_exist():
    toml = DEPLOY_CONFIGS / "no_such_file.toml"
    result = runner.invoke(app, f"deploy {toml}")

    assert "No image found" in result.stdout
    assert result.exit_code == 1


def test_no_image():
    toml = DEPLOY_CONFIGS / "no_image.toml"
    result = runner.invoke(app, f"deploy {toml}")

    assert ("No image found" in result.stdout) or (
        "Something went wrong" in result.stdout
    )
    assert result.exit_code == 1
