from pathlib import Path

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

    assert "No image found" in result.stdout
    assert result.exit_code == 1


def test_flask_one():
    toml = CONFIGS / "flask_one.toml"
    result = runner.invoke(app, f"deploy {toml}")
    print(result.stdout)

    assert result.exit_code == 0
    assert "Installing App" in result.stdout
    assert "deployed as" in result.stdout
