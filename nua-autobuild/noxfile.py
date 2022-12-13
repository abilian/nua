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
    session.run("pytest", "--tb=short")


def _install(session: nox.Session):
    deps = ["../nua-lib", "../nua-runtime"]
    session.run("pip", "install", "-q", *deps)
    session.run("poetry", "install", external=True)
    session.run("pip", "check", external=True)
    session.run("poetry", "check", external=True)
