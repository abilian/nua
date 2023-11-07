import nox
from nox import session

PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]

nox.options.reuse_existing_virtualenvs = True


@session
def lint(session: nox.Session) -> None:
    session.install("--no-cache-dir", ".")
    session.install("abilian-devtools")
    # Temp (hopefully)
    session.install("types-PyYAML")
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    session.install("--no-cache-dir", ".")
    session.install("pytest")
    session.run("pytest", "--tb=short", external=True)
