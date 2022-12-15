import nox
from nox import session

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]

nox.options.reuse_existing_virtualenvs = True


@session
def lint(session: nox.Session) -> None:
    _install(session)
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    _install(session)
    session.run("pytest", "--tb=short")


def _install(session: nox.Session):
    session.run("poetry", "export", "--output=requirements.txt", "--without-hashes", external=True)
    session.install("-r", "requirements.txt")
    session.run("pip", "check")
    session.run("poetry", "check", external=True)
