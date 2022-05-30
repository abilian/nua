from nua_cli.main import app
from typer.testing import CliRunner

from .utils import force_start, force_stop

runner = CliRunner()


def test_help():
    result = runner.invoke(app, "server --help")
    assert result.exit_code == 0
    for cmd in "restart start status stop".split():
        assert f"  {cmd}" in result.stdout.split("Commands:", maxsplit=1)[-1]


def test_stop():
    rep1 = "Stopping Nua server"
    rep2 = "PID file not found"
    result = runner.invoke(app, "server stop")
    assert result.exit_code == 0
    assert rep1 in result.stdout or rep2 in result.stdout
    result = runner.invoke(app, "server stop")
    assert rep2 in result.stdout


def test_start():
    rep1 = "Starting Nua server"
    result = runner.invoke(app, "server start")
    assert result.exit_code == 0
    assert rep1 in result.stdout


def test_restart():
    force_start(runner)
    rep1 = "Stopping Nua server"
    rep2 = "PID file not found"
    rep3 = "Starting Nua server"
    result = runner.invoke(app, "server restart")
    assert result.exit_code == 0
    assert rep1 in result.stdout or rep2 in result.stdout
    assert rep3 in result.stdout
    force_start(runner)


def test_status_1():
    force_stop(runner)
    rep1 = "PID file not found"
    rep2 = "not running"
    result = runner.invoke(app, "server stop")
    assert result.exit_code == 0
    result = runner.invoke(app, "server status")
    assert result.exit_code == 0
    assert rep1 in result.stdout and rep2 in result.stdout


def test_status_ok():
    force_stop(runner)
    force_start(runner)
    rep1 = "Nua orchestrator is running with PID"
    result = runner.invoke(app, "server status")
    assert result.exit_code == 0
    assert rep1 in result.stdout
