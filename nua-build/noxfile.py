import nox

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]

nox.options.reuse_existing_virtualenvs = True


@nox.session(python=PYTHON_VERSIONS, venv_backend="venv")
def lint(session: nox.Session) -> None:
    _install(session)
    session.run("pip", "check", external=True)
    session.run("make", "lint", external=True)


@nox.session(python=PYTHON_VERSIONS, venv_backend="venv")
def pytest(session: nox.Session) -> None:
    session.run("pytest", "--tb=short", external=True)


def _install(session):
    session.run("poetry", "install", "--sync", external=True)
    with session.chdir("../nua-lib"):
        session.run("poetry", "install", external=True)
    with session.chdir("../nua-runtime"):
        session.run("poetry", "install", external=True)
    with session.chdir("../nua-selfbuilder"):
        session.run("poetry", "install", external=True)
