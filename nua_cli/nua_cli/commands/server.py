"""CLI command to start/stop the orchestrator server.

Actually, it is the same to call from nua-cli:
    "nua server start"
or from nua-orchestrator:
    "nua-orchestrator start"
"""
import typer

# NOTE: it's probably the only situation where
# "import nua_orchestrator" is required.
try:
    from nua_orchestrator.main import (
        restart_server,
        start_server,
        status_server,
        stop_server,
    )

    ORC_READY = True
except ModuleNotFoundError:
    ORC_READY = False

app = typer.Typer()


def assert_orchestrator_pkg():
    if not ORC_READY:
        typer.secho("Package nua_orchestrator not found.", bold=True, err=True)
        raise typer.Abort(1)


@app.command()
def start() -> int:
    assert_orchestrator_pkg()
    return start_server()


@app.command()
def stop() -> int:
    assert_orchestrator_pkg()
    return stop_server()


@app.command()
def restart() -> int:
    assert_orchestrator_pkg()
    return restart_server()


@app.command()
def status() -> int:
    assert_orchestrator_pkg()
    return status_server()


if __name__ == "__main__":
    app()
