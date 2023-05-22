import nox
from nox import session

PYTHON_VERSIONS = ["3.10", "3.11"]

nox.options.reuse_existing_virtualenvs = True

# DEPS = []


@session
def lint(session: nox.Session) -> None:
    session.install(".")
    session.install("abilian-devtools")
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    session.install(".")
    session.install("pytest")
    session.run("pytest", "--tb=short")
