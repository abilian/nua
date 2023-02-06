import nox
from nox import session

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]
# DEPS = ["../nua-lib", "../nua-agent", "../nua-autobuild"]

nox.options.reuse_existing_virtualenvs = True


@session
def lint(session: nox.Session) -> None:
    _install(session)
    session.run("make", "lint", external=True)


@session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    _install(session)
    session.run("pytest", "--tb=short", external=True)


def _install(session):
    session.run("bash", "../uninstall-nua.sh", external=True)
    session.run("poetry", "install", "--quiet", external=True)
    session.run("pip", "check", external=True)
    session.run("poetry", "check", external=True)
