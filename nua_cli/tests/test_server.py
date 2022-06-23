from typer.testing import CliRunner

from nua_cli.main import app

from .utils import force_start, force_stop

runner = CliRunner()


def test_help():
    result = runner.invoke(app, "server --help")

    assert result.exit_code == 0
    for cmd in ["restart", "start", "status", "stop"]:
        assert f"  {cmd}" in result.stdout.split("Commands:", maxsplit=1)[-1]


def test_stop_1():
    runner = CliRunner()
    rep1 = "Stopping Nua server"
    rep2 = "PID file not found"

    result = runner.invoke(app, "server stop")

    assert result.exit_code == 0
    assert rep1 in result.stdout or rep2 in result.stdout


def test_stop_2():
    runner = CliRunner()
    rep2 = "PID file not found"
    runner.invoke(app, "server stop")

    result = runner.invoke(app, "server stop")

    assert rep2 in result.stdout


def test_start():
    runner = CliRunner()
    rep1 = "Starting Nua server"

    result = runner.invoke(app, "server start")

    assert result.exit_code == 0
    assert rep1 in result.stdout


def test_restart():
    force_start()
    runner = CliRunner()
    rep1 = "Stopping Nua server"
    rep2 = "PID file not found"
    rep3 = "Starting Nua server"

    result = runner.invoke(app, "server restart")

    assert result.exit_code == 0
    assert rep1 in result.stdout or rep2 in result.stdout
    assert rep3 in result.stdout
    force_start()


def test_status_1():
    force_stop()
    runner = CliRunner()

    result = runner.invoke(app, "server stop")

    assert result.exit_code == 0


def test_status_2():
    force_stop()
    runner = CliRunner()
    rep1 = "PID file not found"
    rep2 = "not running"
    runner.invoke(app, "server stop")

    result = runner.invoke(app, "server status")

    assert result.exit_code == 0
    assert rep1 in result.stdout and rep2 in result.stdout


def test_status_ok():
    force_start()
    runner = CliRunner()
    rep1 = "Nua orchestrator is running with PID"

    result = runner.invoke(app, "server status")

    assert result.exit_code == 0
    assert rep1 in result.stdout
