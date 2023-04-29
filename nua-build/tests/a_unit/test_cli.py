from unittest import skip

import pytest
from cleez.testing import CliRunner

from nua.build import __version__


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def app():
    """Temp workaround while we work on a new CliRunner"""

    from nua.build.main import app

    class App:
        name = "nua-build"

        def main(self, *args, **kw):
            app()

    return App()


def test_version_string():  # noqa
    version_split = __version__.split(".")

    assert len(version_split) >= 2


#
# These tests fail, probably because of a bug in the test runner.
#
@skip
def test_version(app, runner):
    result = runner.invoke(app, "--version")
    assert result.exit_code == 0
    assert "nua-build version:" in result.stdout
    assert __version__ in result.stdout


@skip
def test_version_short(app, runner):
    result = runner.invoke(app, "-V")
    assert result.exit_code == 0
    assert "nua-build version:" in result.stdout
    assert __version__ in result.stdout
