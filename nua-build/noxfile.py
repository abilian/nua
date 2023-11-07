import nox
from nox import session

PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = [
    "lint",
    "pytest",
]


@session
def lint(session: nox.Session) -> None:
    session.install("--no-cache-dir", ".")
    session.install("abilian-devtools")
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    session.install("--no-cache-dir", ".")
    session.install("pytest")
    session.run("pytest", "-vvv", "-m", "not slow", "--tb=short")


@session(python=PYTHON_VERSIONS)
def pytest_all(session: nox.Session):
    session.install("--no-cache-dir", ".")
    session.install("pytest")
    session.run("pytest", "-vvv", "-m", "not slow", "--tb=short")
