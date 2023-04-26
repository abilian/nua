import nox
from nox import session

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = [
    "lint",
    "pytest",
]


@session
def lint(session: nox.Session):
    _install(session)
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session):
    _install(session)
    session.run("pytest", "-vvv", "-m", "not slow", "--tb=short", external=True)


@session(python=PYTHON_VERSIONS)
def pytest_all(session: nox.Session):
    _install(session)
    session.run("pytest", "-vvv", "--tb=short", external=True)


def _install(session: nox.Session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("pip", "check")
    session.run("poetry", "check")
