import nox

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]


@nox.session(python=PYTHON_VERSIONS, venv_backend="venv")
def lint(session: nox.Session) -> None:
    install(session)
    session.run("make", "lint", external=True)


@nox.session(python=PYTHON_VERSIONS, venv_backend="venv")
def pytest(session: nox.Session) -> None:
    install(session)
    session.run("pytest", "--tb=short", external=True)


def install(session: nox.Session):
    session.run("pip", "install", "../nua-lib", "../nua-runtime")
    session.run("poetry", "install", external=True)
    session.run("pip", "check", external=True)
    session.run("poetry", "check", external=True)
