import nox
from nox import session

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]
DEPS = ["../nua-lib", "../nua-runtime", "../nua-autobuild"]

# nox.options.reuse_existing_virtualenvs = True

@session
def lint(session: nox.Session):
    _install(session)
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session):
    _install(session)
    session.run("pytest", "--tb=short", external=True)


def _install(session):
    session.run("poetry", "export", "--output=requirements.txt", "--without-hashes", external=True)
    session.install("-r", "requirements.txt")
    session.install(*DEPS)
    session.run("pip", "check", external=True)
    session.run("poetry", "check", external=True)
