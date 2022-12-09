import nox

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]

nox.options.reuse_existing_virtualenvs = True


@nox.session
def lint(session: nox.Session) -> None:
    _install(session)
    session.run("make", "lint", external=True)


@nox.session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    _install(session)
    session.run("pytest", "--tb=short", external=True)


def _install(session):
    session.run("pip", "install", "../nua-lib", "../nua-runtime", "../nua-autobuild")
    session.run("poetry", "install", external=True)
    session.run("pip", "check", external=True)
    session.run("poetry", "check", external=True)
