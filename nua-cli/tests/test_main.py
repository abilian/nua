# import pytest
#
# from nua_cli.main import cli

# from typer.testing import CliRunner


# @pytest.fixture()
# def runner():
#     return CliRunner()


def test_phony():
    pass


# TODO: make a test runner

# def test_version(runner):
#     result = runner.invoke(cli, "--version")
#     assert result.exit_code == 0
#     assert "Nua CLI version:" in result.stdout
#
#
# def test_bad_arg(runner):
#     result = runner.invoke(cli, "bad_arg")
#     assert result.exit_code != 0
#
#
# def test_verbose(runner):
#     result = runner.invoke(cli, "--verbose")
#     assert result.exit_code != 0
#
#     result = runner.invoke(cli, "-v")
#     assert result.exit_code != 0
