from typer.testing import CliRunner

from nua_build.main import app

runner = CliRunner()


def test_list_0():
    result = runner.invoke(app, "list")

    assert result.exit_code == 0
