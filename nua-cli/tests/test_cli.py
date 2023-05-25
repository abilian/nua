import pytest
from cleez.testing import CliRunner
from nua_cli.main import get_cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def cli():
    return get_cli()


def test_version(cli, runner):
    result = runner.invoke(cli, "--version")
    assert result.exit_code == 0
    assert cli.version in result.stdout
    assert "Usage:" in result.stdout


def test_bad_arg(cli, runner):
    result = runner.invoke(cli, "bad_arg")
    assert result
    # FIXME
    # assert result.exit_code != 0


def test_verbose(cli, runner):
    result = runner.invoke(cli, "--verbose")
    assert result.exit_code == 0

    result = runner.invoke(cli, "-v")
    assert result.exit_code == 0
