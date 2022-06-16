from typer.testing import CliRunner

from nua_build.main import app

runner = CliRunner()


def test_dump_all_settings_0():
    result = runner.invoke(app, "dump_all_settings")

    assert result.exit_code == 0


def test_dump_nua_settings_0():
    result = runner.invoke(app, "dump_nua_settings")

    assert result.exit_code == 0


def test_load_nua_settings():
    return
