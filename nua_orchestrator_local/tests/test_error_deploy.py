import os
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from nua_orchestrator_local.main import app
from nua_orchestrator_local.scripts.test_replace_domain import replace_file

runner = CliRunner()

DEPLOY_CONFIGS = Path(__file__).parent / "deploy_configs"
REPLACE_DOMAIN = Path(__file__).parent / "REPLACE_DOMAIN"

os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


def test_no_exist():
    no_file = DEPLOY_CONFIGS / "no_such_file.toml"

    result = runner.invoke(app, f"deploy {no_file}")

    assert "No image found" in result.stdout
    assert result.exit_code == 1


def test_no_image():
    orig_file = DEPLOY_CONFIGS / "no_image.toml"
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        toml = replace_file(REPLACE_DOMAIN, orig_file, tmp_dir)

        result = runner.invoke(app, f"deploy {orig_file}")

        assert ("No image found" in result.stdout) or (
            "Something went wrong" in result.stdout
        )
        assert result.exit_code == 1
