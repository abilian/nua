import pytest
from cleez.testing import CliRunner
from devtools import debug

from nua.build import __version__
from nua.build.main import main


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def app():
    """Temp workaround while we work on a new CliRunner"""

    class App:
        name = "nua-build"

        def main(self, *args, **kw):
            main()

    return App()


def test_version_string():  # noqa
    version_split = __version__.split(".")

    assert len(version_split) >= 2


def test_version(app, runner):
    result = runner.invoke(app, "--version")
    debug(result.stdout)
    assert result.exit_code == 0
    assert "nua-build version:" in result.stdout
    assert __version__ in result.stdout


def test_version_short(app, runner):
    result = runner.invoke(app, "-V")
    assert result.exit_code == 0
    assert "nua-build version:" in result.stdout
    assert __version__ in result.stdout


def test_bad_arg(app, runner):
    result = runner.invoke(app, "bad_arg")
    assert result.exit_code == 1


def test_verbose(app, runner):
    result = runner.invoke(app, "--verbose")
    assert result.exit_code == 1


def test_verbose_short(app, runner):
    result = runner.invoke(app, "-v")
    assert result.exit_code == 1
