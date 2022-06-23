from typer.testing import CliRunner

from nua_cli import __version__
from nua_cli.main import app


def test_version_string():
    result = __version__.split(".")

    assert len(result) == 3


def test_main():
    runner = CliRunner()
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "version:" in result.stdout
    assert "Usage:" in result.stdout
    assert "Try 'nua --help'" in result.stdout


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, "--version")

    assert result.exit_code == 0
    assert "Nua CLI version:" in result.stdout
    assert __version__ in result.stdout


def test_version_short():
    runner = CliRunner()
    result = runner.invoke(app, "-V")

    assert result.exit_code == 0
    assert "Nua CLI version:" in result.stdout
    assert __version__ in result.stdout


def test_bad_arg():
    runner = CliRunner()
    result = runner.invoke(app, "bad_arg")

    assert result.exit_code == 2


def test_verbose():
    "verbose currently not used"
    runner = CliRunner()
    result = runner.invoke(app, "--verbose")

    assert result.exit_code == 0


def test_verbose_short():
    "verbose currently not used"
    runner = CliRunner()
    result = runner.invoke(app, "-v")

    assert result.exit_code == 0
