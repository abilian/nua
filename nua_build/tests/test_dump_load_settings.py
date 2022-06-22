"""tests for 'nuad show' and 'nuad load'

WIP to be continued...
"""
from typer.testing import CliRunner

from nua_build.main import app


def test_list_all_settings_0():
    runner = CliRunner()
    result = runner.invoke(app, "settings show --all")

    assert result.exit_code == 0


def test_dump_nua_settings_1():
    runner = CliRunner()
    result = runner.invoke(app, "settings show")

    assert result.exit_code == 0


def test_dump_nua_settings_2():
    runner = CliRunner()
    result = runner.invoke(app, "settings show nua")

    assert result.exit_code == 0


def test_dump_nua_settings_3():
    runner = CliRunner()
    result = runner.invoke(app, "settings show nua --json")

    assert result.exit_code == 0


def test_dump_nua_settings_3():
    runner = CliRunner()
    result = runner.invoke(app, "settings show nua --toml")

    assert result.exit_code == 0


def test_load_nua_settings():
    return
