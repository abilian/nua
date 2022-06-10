import typer

# NOTE: it's probably the only situation where
# "import nua_orchestrator" is required.
try:
    import nua_orchestrator as orc

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
    return orc.start()


@app.command()
def stop() -> int:
    assert_orchestrator_pkg()
    return orc.stop()


@app.command()
def restart() -> int:
    assert_orchestrator_pkg()
    return orc.restart()


@app.command()
def status() -> int:
    assert_orchestrator_pkg()
    return orc.status()


if __name__ == "__main__":
    app()
