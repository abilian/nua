import os
from pathlib import Path

from typer.testing import CliRunner

from nua.orchestrator.cli.main import app

runner = CliRunner()

DEPLOY_CONFIGS = Path(__file__).parent / "deploy_configs"
REPLACE_DOMAIN = Path(__file__).parent / "REPLACE_DOMAIN"

os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


def test_no_exist():
    """Test the situation when the file passed as argument does not exist."""
    no_file = DEPLOY_CONFIGS / "no_such_file.toml"

    result = runner.invoke(app, f"deploy {no_file}")

    assert "No image found" in result.stdout
    assert result.exit_code == 1


def test_no_image():
    """Test the situation when the configuration file declare a non-existing
    image file."""
    deploy_file = DEPLOY_CONFIGS / "no_image.toml"

    result = runner.invoke(app, f"deploy {deploy_file}")

    assert ("No image found" in result.stdout) or (
        "Something went wrong" in result.stdout
    )
    assert result.exit_code == 1
