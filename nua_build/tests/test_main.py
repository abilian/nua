from typer.testing import CliRunner

from nua_build import __version__
from nua_build.main import app

runner = CliRunner()


def test_version_string():  # noqa
    # AAA01 no Act block found in test
    version_split = __version__.split(".")

    assert len(version_split) >= 3


def test_main():
    runner = CliRunner()
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "version:" in result.stdout
    assert "Usage:" in result.stdout
    assert "Try 'nuad --help'" in result.stdout


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, "--version")

    assert result.exit_code == 0
    assert "Nua build CLI version:" in result.stdout
    assert __version__ in result.stdout


def test_version_short():
    runner = CliRunner()
    result = runner.invoke(app, "-V")

    assert result.exit_code == 0
    assert "Nua build CLI version:" in result.stdout
    assert __version__ in result.stdout


def test_bad_arg():
    runner = CliRunner()
    result = runner.invoke(app, "bad_arg")

    assert result.exit_code == 2


def test_verbose():
    runner = CliRunner()
    result = runner.invoke(app, "--verbose")

    assert result.exit_code == 0


def test_verbose_short():
    runner = CliRunner()
    result = runner.invoke(app, "-v")

    assert result.exit_code == 0
