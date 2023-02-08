import pytest
from typer.testing import CliRunner

from nua_cli.main import app


@pytest.fixture()
def runner():
    return CliRunner()


def test_version(runner):
    result = runner.invoke(app, "--version")
    assert result.exit_code == 0
    assert "Nua CLI version:" in result.stdout


def test_bad_arg(runner):
    result = runner.invoke(app, "bad_arg")
    assert result.exit_code != 0


def test_verbose(runner):
    result = runner.invoke(app, "--verbose")
    assert result.exit_code != 0

    result = runner.invoke(app, "-v")
    assert result.exit_code != 0
