import pytest
from typer.testing import CliRunner

from nua_build import __version__
from nua_build.main import app


@pytest.fixture
def runner():
    return CliRunner()


def test_version_string():  # noqa
    version_split = __version__.split(".")

    assert len(version_split) >= 2


# def test_main():
#     runner = CliRunner()
#     result = runner.invoke(app)
#
#     assert result.exit_code == 0
#     assert "version:" in result.stdout
#     assert "Usage:" in result.stdout
#     assert "Try 'nua-build --help'" in result.stdout


def test_version(runner):
    result = runner.invoke(app, "--version")
    assert result.exit_code == 0
    assert "nua-build version:" in result.stdout
    assert __version__ in result.stdout


def test_version_short(runner):
    result = runner.invoke(app, "-V")
    assert result.exit_code == 0
    assert "nua-build version:" in result.stdout
    assert __version__ in result.stdout


def test_bad_arg(runner):
    result = runner.invoke(app, "bad_arg")
    assert result.exit_code == 1


def test_verbose(runner):
    result = runner.invoke(app, "--verbose")
    assert result.exit_code == 1


def test_verbose_short(runner):
    result = runner.invoke(app, "-v")
    assert result.exit_code == 1
