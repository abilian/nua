from nua_cli import __version__
from nua_cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version_string():
    assert len(__version__.split(".")) == 3


def test_main():
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "version:" in result.stdout
    assert "Usage:" in result.stdout
    assert "Try 'nua --help'" in result.stdout


def test_version():
    result = runner.invoke(app, "--version")
    assert result.exit_code == 0
    assert "Nua CLI version:" in result.stdout
    assert __version__ in result.stdout


def test_version_shord():
    result = runner.invoke(app, "-V")
    assert result.exit_code == 0
    assert "Nua CLI version:" in result.stdout
    assert __version__ in result.stdout


def test_bad_arg():
    result = runner.invoke(app, "bad_arg")
    assert result.exit_code == 2


def test_verbose():
    # verbose currently not used
    result = runner.invoke(app, "--verbose")
    assert result.exit_code == 0


def test_verbose_shord():
    # verbose currently not used
    result = runner.invoke(app, "-v")
    assert result.exit_code == 0
