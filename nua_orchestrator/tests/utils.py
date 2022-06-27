from pathlib import Path
from time import sleep

from typer.testing import CliRunner

from nua_orchestrator import config
from nua_orchestrator.main import app


def force_start():
    runner = CliRunner()
    sleep(0.05)
    runner.invoke(app, "start")
    pid_file = Path(config.read("nua", "server", "pid_file"))  # noqa: S108
    cnt = 500
    while not pid_file.exists() and cnt > 0:
        cnt -= 1
        sleep(0.01)
    if not pid_file.exists():
        raise ValueError("Problem starting server")


def force_stop():
    runner = CliRunner()
    pid_file = Path(config.read("nua", "server", "pid_file"))  # noqa: S108
    runner.invoke(app, "stop")
    # following is required because another process may try at same time to 
    # start the server...
    sleep(0.05)
    cnt = 20
    while pid_file.exists() and cnt > 0:
        cnt -= 1
        sleep(0.01)
    if pid_file.exists():    
        runner.invoke(app, "stop")
    cnt = 500    
    while pid_file.exists() and cnt > 0:
        cnt -= 1
        sleep(0.01)
    if pid_file.exists():
        raise ValueError("Problem stoping server")
