from pathlib import Path
from time import sleep

import pytest
from typer.testing import CliRunner

from nua_cli.main import app


def force_start(runner):
    sleep(0.05)
    runner.invoke(app, "server start")
    pid_file = Path("/tmp/nua/orchestrator.pid")
    cnt = 500
    while not pid_file.exists() and cnt > 0:
        cnt -= 1
        sleep(0.01)
    if not pid_file.exists():
        raise ValueError("Problem starting server")


def force_stop(runner):
    runner.invoke(app, "server stop")
    sleep(0.05)
    pid_file = Path("/tmp/nua/orchestrator.pid")
    cnt = 500
    while pid_file.exists() and cnt > 0:
        cnt -= 1
        sleep(0.01)
    if pid_file.exists():
        raise ValueError("Problem stoping server")
