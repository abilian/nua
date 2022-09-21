from typer.testing import CliRunner

from nua_orchestrator_local import __version__
from nua_orchestrator_local.main import app

runner = CliRunner()


def test_version_string():  # noqa
    # AAA01 no Act block found in test
    version_split = __version__.split(".")

    assert len(version_split) >= 2


def test_version():
    runner = CliRunner()

    result = runner.invoke(app, "--version")

    assert result.exit_code == 0
    assert "Nua orchestrator local" in result.stdout
    assert __version__ in result.stdout


def test_version_short():
    runner = CliRunner()

    result = runner.invoke(app, "-V")

    assert result.exit_code == 0
    assert "Nua orchestrator local" in result.stdout
    assert __version__ in result.stdout


def test_bad_arg():
    runner = CliRunner()

    result = runner.invoke(app, "bad_arg")

    assert result.exit_code == 2


def test_verbose():
    runner = CliRunner()

    result = runner.invoke(app, "--verbose")

    assert result.exit_code == 2


def test_verbose_short():
    runner = CliRunner()

    result = runner.invoke(app, "-v")

    assert result.exit_code == 2
