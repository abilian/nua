import nox
from nox import session

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]

nox.options.reuse_existing_virtualenvs = True

# DEPS = []


@session
def lint(session: nox.Session) -> None:
    _install(session)
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    _install(session)
    session.run("pytest", "--tb=short")


def _install(session: nox.Session):
    session.install("poetry")
    session.run("poetry", "install", "--quiet")
    session.run("pip", "check")
    session.run("poetry", "check")
