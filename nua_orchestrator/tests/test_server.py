from typer.testing import CliRunner

from nua_orchestrator.main import app

from .utils import force_start, force_stop


def test_help():
    runner = CliRunner()
    result = runner.invoke(app, "--help")

    assert result.exit_code == 0
    for cmd in ["restart", "start", "status", "stop"]:
        assert f"  {cmd}" in result.stdout.split("Commands:", maxsplit=1)[-1]


def test_stop_1():
    runner = CliRunner()
    rep1 = "Stopping Nua server"
    rep2 = "PID file not found"

    result = runner.invoke(app, "stop")

    assert result.exit_code == 0
    assert rep1 in result.stdout or rep2 in result.stdout


def test_stop_2():
    runner = CliRunner()
    rep2 = "PID file not found"
    runner.invoke(app, "stop")

    result = runner.invoke(app, "stop")

    assert rep2 in result.stdout


def test_start():
    runner = CliRunner()
    rep1 = "Starting Nua server"

    result = runner.invoke(app, "start")

    assert result.exit_code == 0
    assert rep1 in result.stdout


def test_restart():
    runner = CliRunner()
    force_start()
    rep1 = "Stopping Nua server"
    rep2 = "PID file not found"
    rep3 = "Starting Nua server"

    result = runner.invoke(app, "restart")

    assert result.exit_code == 0
    assert rep1 in result.stdout or rep2 in result.stdout
    assert rep3 in result.stdout


def test_status_1():
    runner = CliRunner()
    force_stop()

    result = runner.invoke(app, "stop")

    assert result.exit_code == 0


def test_status_2():
    runner = CliRunner()
    force_stop()
    rep1 = "PID file not found"
    rep2 = "not running"
    runner.invoke(app, "stop")

    result = runner.invoke(app, "status")

    assert result.exit_code == 0
    assert rep1 in result.stdout and rep2 in result.stdout


def test_status_ok():
    runner = CliRunner()
    force_start()
    rep1 = "Nua orchestrator is running with PID"

    result = runner.invoke(app, "status")

    assert result.exit_code == 0
    assert rep1 in result.stdout
